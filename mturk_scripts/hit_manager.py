"""Function to create HITs with a given layouts.
"""
import boto3
import datetime
import json
import xmltodict

from string import Template
from typing import Any, Dict, List, Optional

import logger
import utils

_LOGGER = logger.get_logger(__name__)


class TemplateRenderer:
    """Abstract class to represent a template renderer.

    Every template will have its own variables to fill, which are captured
    by the kwargs parameter in function render_template.

    By creating new classes for different templates, it is possible to keep track
    of which template is used for each hit.
    """
    def __init__(self, template_filepath: str = 'templates') -> None:
        self.template_filepath = template_filepath

    def render_template(self, **kwargs):
        with open(self.template_filepath, 'r') as template_file:
            template = Template(template_file.read())
        return template.substitute(**kwargs)


class HITManager:

    def __init__(self, mturk_endpoint: str,
                 aws_access_key: str, aws_secret_key: str, max_hits: int = 99,
                 **kwargs) -> None:
        self.mturk_client = boto3.client(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            service_name='mturk',
            region_name='us-east-1',
            endpoint_url=mturk_endpoint,
        )
        self.max_hits = max_hits

    def create_hit(
            self, rendered_template, hit_type: str = '', hit_lifetime_seconds=3600,
            max_assignments=1, keywords: str = 'iglu',
            auto_approval_delay_seconds: int = 3600, reward: str = "0.80",
            assignment_duration_in_seconds: int = 480,
            title: str = 'random title', description: str = 'random description',
            qualification_type_id: str = None,
            qualification_country_codes: Optional[List[str]] = None,
            **kwargs) -> str:

        common_kwargs = dict(
            LifetimeInSeconds=hit_lifetime_seconds,  # 604800
            MaxAssignments=max_assignments,
            Keywords=keywords,
            AutoApprovalDelayInSeconds=auto_approval_delay_seconds,
        )

        qualifiers = []
        if qualification_type_id is not None:
            qualifiers.append({
                'QualificationTypeId': qualification_type_id,
                'Comparator': 'GreaterThan',
                'IntegerValues': [80]
            })
        if qualification_country_codes is not None:
            # Recommended values US and CA
            qualifiers.append({
                'QualificationTypeId': '00000000000000000071',
                'Comparator': 'In',
                'LocaleValues': [{'Country': country} for country in qualification_country_codes]
            })

        hit = self.mturk_client.create_hit(
            **common_kwargs,
            Reward=reward,
            AssignmentDurationInSeconds=assignment_duration_in_seconds,
            Title=title,
            Description=description,
            Question=rendered_template,
            RequesterAnnotation=json.dumps({'hit_type': hit_type}),
            QualificationRequirements=qualifiers
        )
        hit_id = hit['HIT']['HITId']
        _LOGGER.info(f'HIT created with Id {hit_id}')
        return hit_id

    def get_open_hit_ids(self, hit_type: str) -> List[Dict[str, Any]]:
        """Get hit that are not expired with this @hit_type and that have not been reviewed.

        Returns:
            List[Dict[str, Any]]: _description_
        """
        # TODO use pagination string
        hit_dict = self.mturk_client.list_hits(MaxResults=self.max_hits)['HITs']
        selected_hits = []
        for hit in hit_dict:
            if 'RequesterAnnotation' in hit:
                is_correct_type = json.loads(hit['RequesterAnnotation'])['hit_type'] == hit_type
            else:
                is_correct_type = False
            # Check hit is correct type and reviewable
            if (is_correct_type and hit['HITStatus'] not in ['Disposed'] and
                hit['HITReviewStatus'] not in ['ReviewedAppropriate', 'ReviewedInappropriate'] and
                    not self.is_hit_expired(hit)):
                selected_hits.append(hit['HITId'])

        _LOGGER.info(f"{len(selected_hits)} previous open hits of type {hit_type} returned")
        return selected_hits

    @staticmethod
    def is_hit_expired(hit_dict):
        return datetime.datetime.now().timestamp() >= hit_dict['Expiration'].timestamp()

    def _build_assignment_dict(self, assignment):
        """Extracts answers from Mturk assignment dict returned by boto3 api.

        This method is particular to each template, so subclasses are encouraged to override it.

        Returns:
            A dictionary with the extracted data, or None if there are no Answers in the
            assignment.
        """
        answer = self._parse_xml_response(assignment["Answer"])
        if answer is not None:
            assignment_dict = {}
            assignment_dict['WorkerId'] = assignment['WorkerId']
            assignment_dict["InputInstruction"] = answer
            return assignment_dict
        return None

    def complete_open_assignments(self, hit_ids: List[str]) -> Dict[str, Any]:
        """Get a list of the Assignments that have been submitted for all open hits.

        Reviews and completes the assignments, returning the answers as a dictionary.

        Args:
            hit_ids (List[str]): A list of hit ids to search for assignments and complete.

        Returns:
            dict: Dictionary from hit ids to responses of the assignments for that hit.
            If there is more than one assignment for the HIT, only the value of the last valid
            one is retrieved.
        """
        results = {}

        for hit_id in hit_ids:

            # Get a list of the Assignments that have been submitted
            submitted_assignments = self.mturk_client.list_assignments_for_hit(
                HITId=hit_id,
                AssignmentStatuses=['Submitted']
            )
            if submitted_assignments["NumResults"] == 0:
                continue

            assignments = submitted_assignments['Assignments']
            # Retrieve the attributes for each Assignment
            for assignment in assignments:
                _LOGGER.info(f"Processing {assignment['AssignmentId']} assignment for HIT {hit_id}")
                assignment_dict = self._build_assignment_dict(assignment)
                if assignment_dict is not None:
                    qualified = self.verify_new_assignment(assignment_dict)
                    assignment_dict['IsHITQualified'] = qualified
                    results[hit_id] = assignment_dict
                    self.close_assignment(assignment['AssignmentId'], hit_id, qualified)
        return results

    @staticmethod
    def _parse_xml_response(xml_answer: str):
        xml_doc = xmltodict.parse(xml_answer)
        # Parse the XML response
        if type(xml_doc["QuestionFormAnswers"]["Answer"]) is list:
            # Multiple fields in HIT layout
            for answer_field in xml_doc["QuestionFormAnswers"]["Answer"]:
                input_field = answer_field["QuestionIdentifier"]
                if input_field == 'InputInstructionSingleTurn':
                    return answer_field["FreeText"]
        else:
            # One field found in HIT layout
            input_field = xml_doc["QuestionFormAnswers"]["Answer"]["QuestionIdentifier"]
            if input_field == "InputInstructionSingleTurn":
                return xml_doc["QuestionFormAnswers"]["Answer"]["FreeText"]

        return None

    def verify_new_assignment(self, assignment_dict) -> bool:
        """Asserts whether the assignment should be approved or not.

        Args:
            assignment_dict (dictionary): A dictionary representation of the
                assignment, with at least keys 'InputInstruction'.

        Returns:
            bool: _description_
        """
        qualified = False
        if 'InputInstruction' in assignment_dict.keys():
            instruction = assignment_dict['InputInstruction']
            if (instruction is not None and
                    len(instruction.strip()) > 5 and
                    utils.is_english(instruction)):
                qualified = True
        return qualified

    def close_assignment(self, assignment_id: str, hit_id: str, is_qualified: bool):
        """Approve or not the assignment based on its qualification, and delete the hit.

        Current implementation approves all assignments, and relies on hits having a single
        assignment each.
        """
        self.mturk_client.approve_assignment(
            AssignmentId=assignment_id,
            OverrideRejection=False
        )

        self.mturk_client.delete_hit(HITId=hit_id)
        _LOGGER.info(f"Assignment {assignment_id} and {hit_id} closed.")
