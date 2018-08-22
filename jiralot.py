from jira import JIRA
import re
import datetime
import base64
import logging
import json

logging.basicConfig(format="%(levelname)s - %(message)s", level=logging.DEBUG)
with open("bin/session.json") as json_data_file:
    session = json.load(json_data_file)


class JiraNavigate:
    """
    Wraps the JIRA module to easily obtain information on a project. The underlying
    communication requires login details and a REST interface.
    """

    def __init__(self):
        self.jira = JIRA(basic_auth=(session["username"], base64.b64decode(session["password"])),
                         options={'server': session["server"]})

    def get_issues(self, jql):
        logging.debug("JQL: %s" % jql)
        return self.jira.search_issues(jql)

    def get_changelog(self, issue):
        issue = self.jira.issue(self.get_key(issue), expand='changelog')
        return issue.changelog

    def get_comments(self, issue):
        return self.jira.comments(issue)

    @staticmethod
    def get_title(issue):
        return "[%s] %s" % (issue.key, issue.fields.summary)

    @staticmethod
    def get_assignee(issue):
        if issue.fields.assignee is None:
            return ""
        else:
            return issue.fields.assignee.displayName

    @staticmethod
    def get_key(issue):
        return issue.key

    @staticmethod
    def get_summary(issue):
        return issue.fields.summary

    @staticmethod
    def get_components(issue):
        return issue.fields.components

    def get_created_date(self, issue):
        return self.to_datetime(issue.fields.created)

    def get_updated_date(self, issue):
        return self.to_datetime(issue.fields.updated)

    @staticmethod
    def get_labels(issue):
        return issue.fields.labels

    @staticmethod
    def get_story_points(issue):
        story_points = issue.fields.customfield_10103
        if story_points > 0:
            return story_points
        return 0

    def rerank(self, sorted_backlog):
        for pair in zip(sorted_backlog, sorted_backlog[1:]):
            key1 = self.get_key(pair[0]["issue"])
            key2 = self.get_key(pair[1]["issue"])
            self.jira.rank(key2, key1)

    def count_story_points(self, issues):
        points = 0
        for issue in issues:
            points += self.get_story_points(issue)
        return points
    
    def sprint_name(self, sprint_id):
        return self.jira.sprint(sprint_id)

    def sprint_committed_points(self, sprint_id, board_name):
        jql = "Sprint = {:d} AND issueFunction not in " \
              "addedAfterSprintStart(\"{}\", \"{}\")".format(sprint_id,
                                                             board_name,
                                                             self.sprint_name(sprint_id))
        logging.debug("JQL sprint_committed_points: {}".format(jql))
        committed_issues = self.jira.search_issues(jql)
        return self.count_story_points(committed_issues)

    def sprint_completed_points(self, sprint_id, board_name):
        jql = "issueFunction in completeInSprint(\"{}\", \"{}\")".format(board_name, self.sprint_name(sprint_id))
        logging.debug("JQL sprint_completed_points: {}".format(jql))
        completed_issues = self.jira.search_issues(jql)
        return self.count_story_points(completed_issues)

    def sprint_interrupt_points(self, sprint_id, board_name):
        jql = "(issueFunction in addedAfterSprintStart(\"{}\", \"{}\"))" \
              "AND resolution = Unresolved ".format(board_name,
                                                    self.jira.sprint(sprint_id))
        logging.debug("JQL sprint_interrupt_points: {}".format(jql))
        interrupt_issues = self.jira.search_issues(jql)
        return self.count_story_points(interrupt_issues)

    def sprint_incomplete_points(self, sprint_id, board_name):
        jql = "(Sprint = {:d} AND issueFunction not in addedAfterSprintStart(\"{}\", \"{}\")) " \
              "AND resolution = Unresolved ".format(sprint_id,
                                                    board_name,
                                                    self.sprint_name(sprint_id))
        logging.debug("JQL sprint_incomplete_points: %s" % jql)
        incomplete_issues = self.jira.search_issues(jql)
        return self.count_story_points(incomplete_issues)

    @staticmethod
    def to_datetime(str_date):
        """
        Takes the text-based timestamp from the JSON document and converts it to a Python datetime.
        :param str_date: The string version of the date
        :return: a valid Python datetime object
        """
        p = re.compile("(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)\.\d+\+(\d+)")
        m = p.match(str_date)
        return datetime.datetime(
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3)),
            (int(m.group(4)) + int(m.group(7))) % 24,
            int(m.group(5)),
            int(m.group(6))
        )
