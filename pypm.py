from jiralot import JiraNavigate
import logging
import json
from datetime import datetime, timedelta

# Configuration and initialisation
logging.basicConfig(level=logging.DEBUG)
with open("bin/usersettings.json") as json_data_file:
    data = json.load(json_data_file)
cat = JiraNavigate()

increments = data["ranking"]["increments"]
priority_labels = data["ranking"]["priority_labels"]
manual_weights = data["ranking"]["manual_weights"]
team_engineers = sorted(data["engineers"])


def score(issue):
    """
    For a given issue, give it a score based on a set of rules that keep into account
    issue attributes such as labels, sizing and manual escalation.
    :param issue: A Jira issue.
    :return issue_score: a weighted score for the issue based on issue properties
    """
    issue_score = 0

    def manual_weighting_increment(key):
        """
        Sometimes it is necessary to push up the priority for an issue that cannot be inferred
        from issue properties. A manually compiled dictionary of issue keys can be used to
        add custom weights to a score.
        :param key: The Jira issue key
        :return: A custom weight allocated to the issue
        """
        if key in manual_weights:
            return manual_weights[key]
        return 0

    def label_increment(label_text):
        """
        Return a score that is associated with this label.
        :param label_text: The label being interrogated.
        :return: An integer score associated with this label
        """
        increment = 0
        if label_text.lower() in priority_labels:
            increment = priority_labels[label_text.lower()]
        return increment

    def readiness_increment(points):
        """
        Returns a bonus increment if the issue is estimated an broken down to a
        granular enough level to be started.
        :param points: Number of story points estimated for the issue
        :return: A readiness score
        """
        increment = 0
        if 0 < points <= 3:
            increment = increments["scoped"] + (3-points)
        if 3 < points <= 5:
            increment = increments["scoped"]
        return increment

    for label in cat.get_labels(issue):
        issue_score += label_increment(label)

    issue_score += readiness_increment(cat.get_story_points(issue))
    issue_score += manual_weighting_increment(cat.get_key(issue))

    return issue_score


def score_all(jira_issues):
    """
    Iterates over the list of Jira issues and assigns a score to each based on its properties.
    :param jira_issues: a list of jira issues
    :return: a list of issues with metadata including its weighted score
    """
    scored_issues = []
    for jira_issue in jira_issues:
        scored_entry = {
            "issue": jira_issue,
            "score": score(jira_issue)
        }
        scored_issues.append(scored_entry)

    return scored_issues


def format_date(date):
    """
    Formats a date to be usable in a JQL query.
    :param date: The datetime object to format
    :return: A JQL-friendly string with "yyyy/MM/dd HH:mm" format
    """
    return datetime.strftime(date, '%Y/%m/%d %H:%M')


def assignee_comment_statistics():
    """
    Information about the recent activity of issue assignees.
    :return: A dictionary containing statistics about an assignee's recent activity on their issues.
    """
    yesterday = datetime.today() + timedelta(-1)
    yesterday = datetime(yesterday.year, yesterday.month, yesterday.day, 12, 0)
    jql = "project = CAT AND updated >= \"{}\"".format(format_date(yesterday))
    issues = cat.get_issues(jql)

    stats = dict(jql=jql, reference_time=format_date(yesterday), authors={})
    for issue in issues:
        comments = cat.get_comments(issue)
        assignee = cat.get_assignee(issue)
        for comment in comments:
            comment_updated = cat.to_datetime(comment.updated)
            author = comment.author.displayName
            if (comment_updated > yesterday) and (author == assignee):
                entry = {
                    "key": issue.key,
                    "comment_time": format_date(comment_updated)
                }

                if author not in stats["authors"]:
                    stats["authors"][author] = []
                stats["authors"][author].append(entry)

    return stats


def assignee_activity_summary_str(comment_stats):
    """
    Summarise the level of activity for team engineers.
    :param comment_stats: The stats provided by assignee_comment_statistics
    :return: A formatted summary string
    """
    message = "Comments made by assignees since: {}\n".format(comment_stats["reference_time"])
    for engineer in team_engineers:
        if engineer in comment_stats["authors"]:
            message = message + "{:>32}: {:d}\n".format(engineer, len(comment_stats["authors"][engineer]))
        else:
            message = message + "{:>32}: {:d}\n".format(engineer, 0)
    return message


def get_sprint_statistics(sprint_id):
    """
    Where story points are used to track sprints, this function helps to determine the efficiency and accuracy
    of a team.
    :param sprint_id: The specific sprint id to be interrogated must be provided (integer)
    :return: A table containing metadata about the sprint, as well as information about committed, completed,
    incomplete and interrupt point tallies.
    """
    board_name = data["board_name"]
    sprint_name = "{}".format(cat.sprint_name(sprint_id))
    print(sprint_name)
    dat = dict(board_name=board_name, sprint_name=sprint_name, sprint_id=sprint_id, statistics={
        'committed': cat.sprint_committed_points(sprint_id, board_name),
        'completed': cat.sprint_completed_points(sprint_id, board_name),
        'interrupt': cat.sprint_interrupt_points(sprint_id, board_name),
        'incomplete': cat.sprint_incomplete_points(sprint_id, board_name)})
    return dat


def __main__():

    # Daily Check-In
    stats = assignee_comment_statistics()
    print(assignee_activity_summary_str(stats))

    # Re-rank
    if data["ranking"]["enabled"]:
        scored_backlog = score_all(cat.get_issues(data["ranking"]["filter"]))
        sorted_backlog = sorted(scored_backlog, key=lambda k: k["score"])
        cat.rerank(sorted_backlog)


# __main__()
