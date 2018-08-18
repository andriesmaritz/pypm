from tkinter import *
import pypm
import json
import logging

logging.basicConfig(format="%(levelname)s - %(message)s", level=logging.DEBUG)


class JiraAnalyticsGUI:
    def __init__(self):
        self.root = Tk()
        self.root.title("Analytics for Product Management")

        self.frame_actions = Frame(self.root)
        self.frame_actions.grid(column=0, row=0)

        self.frame_output = Frame(self.root)
        self.frame_output.grid(column=1, row=0)

        self.actions = []
        self.add_actions()

        self.txt_output = Text(self.frame_output, width=100, height=30)
        self.txt_output.grid(column=0, row=0)

    def add_actions(self):
        self.actions.append(Button(self.frame_actions, width=20, text="Close", command=self.root.quit))
        self.actions.append(Button(self.frame_actions, width=20, text="Daily check-in", command=self.daily_check_in))
        self.actions.append(Button(self.frame_actions, width=20, text="Sprint stats", command=self.sprint_statistics))
        self.actions.append(Button(self.frame_actions, width=20, text="Rerank", command=self.rerank_backlog))

        counter = 0
        for action in self.actions:
            action.grid(column=0, row=counter)
            counter += 1

    def run(self):
        self.root.mainloop()

    def update_output(self, content):
        self.txt_output.delete('1.0', '200.0')
        self.txt_output.insert(INSERT, content)

    def daily_check_in(self):
        stats = pypm.assignee_comment_statistics()
        text = pypm.assignee_activity_summary_str(stats)
        self.update_output(text)

    def sprint_statistics(self):
        stats = pypm.get_sprint_statistics(907)
        text = json.dumps(stats, indent=4)
        self.update_output(text)

    def rerank_backlog(self):
        scored_backlog = pypm.score_all(pypm.cat.get_issues(pypm.data["ranking"]["filter"]))
        sorted_backlog = sorted(scored_backlog, key=lambda k: k["score"])
        pypm.cat.rerank(sorted_backlog)

        text = ""
        for entry in sorted_backlog:
            text = text + "Score [{}]: {}\n".format(entry["score"], pypm.cat.get_title(entry["issue"]))
        self.update_output(text)


def __main__():
    my_gui = JiraAnalyticsGUI()
    my_gui.run()


__main__()
