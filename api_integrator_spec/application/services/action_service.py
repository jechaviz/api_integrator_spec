from api_integrator_spec.application.interfaces.api_parser_interface import ApiParserInterface

class ActionService:
    def __init__(self, api_parser: ApiParserInterface):
        self.api_parser = api_parser

    def perform_action(self, action_id, values):
        return self.api_parser.action_requests(action_id, values)
