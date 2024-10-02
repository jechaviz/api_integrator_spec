from api_integrator_spec.domain.services.api_parser import ApiParser

class ActionService:
    def __init__(self, api_parser: ApiParser):
        self.api_parser = api_parser

    def perform_action(self, action_id, values):
        return self.api_parser.action_requests(action_id, values)
