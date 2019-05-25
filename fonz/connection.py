from typing import Sequence, List, Dict, Any
from utils import compose_url
import requests
import logging
import sys

JsonDict = Dict[str, Any]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


class Fonz:

    def __init__(self, url: str, client_id: str, client_secret: str,
                 project: str, branch: str, port: int, api: str):
        """Instantiate Fonz and save authentication details and branch."""
        if url[-1] == '/':
            self.url = '{}:{}/api/{}/'.format(url[:-1], port, api)
        else:
            self.url = '{}:{}/api/{}/'.format(url, port, api)

        self.client_id = client_id
        self.client_secret = client_secret
        self.branch = branch
        self.project = project
        self.client = None
        self.headers = None

        logging.info('Instantiated Fonz object for url: {}'.format(url))

    def connect(self) -> None:
        """Authenticate, start a dev session, check out specified branch."""

        logging.info('Authenticating Looker credentials.')

        login = requests.post(
            url=compose_url(self.url, 'login'),
            data={
                'client_id': self.client_id,
                'client_secret': self.client_secret
                })

        access_token = login.json()['access_token']
        self.headers = {'Authorization': 'token {}'.format(access_token)}

        logging.info('Updating session to use development workspace.')

        update_session = requests.patch(
            url=compose_url(self.url, 'session'),
            headers=self.headers,
            json={'workspace_id': 'dev'})

        logging.info('Setting git branch to: {}'.format(self.branch))

        update_branch = requests.put(
            url=compose_url(self.url, 'projects', self.project, 'git_branch'),
            headers=self.headers,
            json={'name': self.branch})

    def get_explores(self) -> List[JsonDict]:
        """Get all explores from the LookmlModel endpoint."""

        logging.info('Getting all explores in Looker instance.')

        models = requests.get(
            url=compose_url(self.url, 'lookml_models'),
            headers=self.headers)

        explores = []

        logging.info('Filtering explores for project: {}'.format(self.project))

        for model in models.json():
            if model['project_name'] == self.project:
                for explore in model['explores']:
                    explores.append({
                        'model': model['name'],
                        'explore': explore['name']
                        })

        return explores

    def get_explore_dimensions(self, explore: JsonDict) -> List[str]:
        """Get dimensions for an explore from the LookmlModel endpoint."""

        logging.info('Getting dimensions for {}'.format(explore['explore']))

        lookml_explore = requests.get(
            url=compose_url(
                self.url,
                'lookml_models',
                explore['model'],
                'explores',
                explore['explore']),
            headers=self.headers)

        dimensions = []

        for dimension in lookml_explore.json()['fields']['dimensions']:
            dimensions.append(dimension['name'])

        explore['dimensions'] = dimensions

        return explore

    def get_dimensions(self, explores: List[JsonDict]) -> List[JsonDict]:
        """Finds the dimensions for all explores"""
        for explore in explores:
            explore = self.get_explore_dimensions(explore)

        return explores

    def create_query(self, explore: JsonDict) -> str:
        """Build a Looker query using all the specified dimensions."""

        logging.info('Creating query for {}'.format(explore['explore']))

        query = requests.post(
            url=compose_url(self.url, 'queries'),
            headers=self.headers,
            json={
                'model': explore['model'],
                'view': explore['explore'],
                'fields': explore['dimensions'],
                'limit': 1
            })

        query_id = query.json()['id']

        return query_id

    def run_query(self, query_id: int) -> JsonDict:
        """Run a Looker query by ID and return the JSON result."""

        logging.info('Running query {}'.format(query_id))

        query = requests.get(
            url=compose_url(self.url, 'queries', query_id, 'run', 'json'),
            headers=self.headers)

        return query.json()

    def validate_explores(self, explores: List[JsonDict]) -> None:
        """Take explores and runs a query with all dimensions."""
        errors = False

        for explore in explores:
            query_id = self.create_query(explore)
            query_result = self.run_query(query_id)

            if 'looker_error' in query_result[0]:
                logging.info('Error in explore {}: {}'.format(
                    explore['explore'],
                    query_result[0]['looker_error'])
                )
                errors = True

        if errors:
            sys.exit(1)

    def validate_content() -> JsonDict:
        """Validate all content and return any JSON errors."""
        pass
