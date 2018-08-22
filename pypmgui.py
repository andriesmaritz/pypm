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

    def add_button(self, label, func):
        return Button(self.frame_actions, width=30, text=label, command=func)

    # TODO Input field is created but not accessible/connected
    def add_input_field(self, label, default=0):
        widget = Frame(self.frame_actions)
        w_label = Label(widget, text=label, width=10)
        w_label.grid(column=0, row=0)
        w_input = Entry(widget, text=default, width=20)
        w_input.grid(column=1, row=0)
        return widget

    def add_actions(self):
        self.actions.append(self.add_input_field("Sprint #", 907))
        self.actions.append(self.add_button("Daily check-in", self.daily_check_in))
        self.actions.append(self.add_button("Sprint stats", self.sprint_statistics))
        self.actions.append(self.add_button("Rerank", self.rerank_backlog))
        self.actions.append(self.add_button("Close", self.root.quit))

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
