#!/usr/bin/env python3

import datetime
import json
import os
import tkinter
import tkinter.ttk
from typing import Dict, List, Optional, Tuple

# Name of the program.
NAME = "MiKan"
# Extension for the project files.
EXT = ".prj"
# Root path of the projects.
PATH_ROOT = os.path.dirname(os.path.realpath(__file__))
# Path for saving the projects.
PATH_PROJ = os.path.join(PATH_ROOT, ".proj")
# Key for the tasks not to show.
KEY_HIDDEN = "hidden"
# Allowed levels for tasks.
LEVELS = ["critical", "high", "normal", "low"]
# Whether a weekday is working day [?, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]
WORKING_DAYS = (None, True, True, True, True, True, False, False)
# Default height for components.
BUTTON_HEIGHT = 3
# Default width for components.
BUTTON_WIDTH = 40

# Single root window to keep GUI consistent
ROOT = tkinter.Tk()
ROOT.title(NAME)


def create_window(title: str) -> tkinter.Toplevel:
    """
    Create a child window of the single ROOT instead of a new Tk instance.
    """
    win = tkinter.Toplevel(ROOT)
    win.title(title)
    return win


def parse_date(string: str) -> Optional[datetime.datetime]:
    """
    Parse one date written as "YYYY-MM-DD".
    """
    try:
        return datetime.datetime.strptime(string, "%Y-%m-%d")
    except Exception as error:
        print(f"failed to parse date string: {error}")
        return None


def format_date(date: datetime.datetime) -> str:
    """
    Format one date as "YYYY-MM-DD".
    """
    return date.strftime("%Y-%m-%d")


def distance_date(start: datetime.datetime, end: datetime.datetime) -> int:
    """
    Count the number of working days between two dates (start -> end).
    Returns -1 if start is after end.
    """
    start_date = datetime.date(year=start.year, month=start.month, day=start.day)
    end_date = datetime.date(year=end.year, month=end.month, day=end.day)

    if start_date > end_date:
        return -1

    delta_days = (end_date - start_date).days
    if delta_days == 0:
        return 0

    full_weeks, extra_days = divmod(delta_days, 7)

    # Monday=1, Sunday=7
    start_weekday = start_date.isocalendar()[2]

    working = full_weeks * 5
    for i in range(extra_days):
        weekday = (start_weekday + i - 1) % 7 + 1
        if WORKING_DAYS[weekday]:
            working += 1
    return working


def encode_color(task: dict, today: datetime.datetime) -> Tuple[str, str]:
    """
    Decide the color of one task.
    background: importance
    border: urgency
    """
    rule = {
        "critical": "#B22222",
        "high": "#FFA500",
        "normal": "#FDF5E6",
        "low": "#9ACD32",
    }
    background = rule[task["level"]]

    deadline_dt = parse_date(task["deadline"])
    if deadline_dt is None:
        interval = 9999
    else:
        interval = distance_date(today, deadline_dt)

    if interval <= 1:
        border = "#B22222"
    elif interval <= 3:
        border = "#FFA500"
    else:
        border = background

    return background, border


def list_date(size: int = 30) -> List[str]:
    """
    List the following working dates (today + forward).
    """
    result: List[str] = []
    date = datetime.datetime.now()
    one_day = datetime.timedelta(days=1)
    for _ in range(size):
        if WORKING_DAYS[date.isocalendar()[2]]:
            result.append(format_date(date))
        date += one_day
    return result


class Project(object):
    """
    The management of tasks with GUI.
    """

    def __init__(self, name: str) -> None:
        """
        Start the project with given name. The content must be already initialized.
        """
        self._name = name
        self._path = os.path.join(PATH_PROJ, name + EXT)
        with open(self._path, "r", encoding="utf-8") as fs:
            self._data = json.load(fs)
        self._data["tasks"] = {int(k): v for k, v in self._data["tasks"].items()}
        self._check(self._data)
        self._height = BUTTON_HEIGHT
        self._width = BUTTON_WIDTH
        self._window_main: Optional[tkinter.Toplevel] = None

    def _get_steps(self) -> List[str]:
        """
        Get the defined steps in project.
        """
        return list(self._data["steps"])

    def _get_tasks_in_step(self, step: str) -> Dict[int, dict]:
        """
        Get the tasks which are in the given step.
        """
        return {idx: task for idx, task in self._data["tasks"].items() if task["step"] == step}

    def edit_task(self, idx: int = -1) -> None:
        """
        Start a dialog for editing the task.
        idx < 0 means create a new task.
        """

        def edit(idx_inner: int, i_step: int) -> None:
            title = text_title.get("1.0", tkinter.END).strip()
            assert "\n" not in title, "title cannot contain newline"
            if idx_inner < 0:
                idx_inner = (max(self._data["tasks"].keys()) + 1) if bool(self._data["tasks"]) else 0
            deadline = comb_deadline.get()
            level = comb_level.get()
            if parse_date(deadline) is not None and level in LEVELS:
                step_to_be = (self._get_steps() + [KEY_HIDDEN])[i_step]
                self._data["tasks"][idx_inner] = {
                    "step": step_to_be,
                    "title": title,
                    "text": text_description.get("1.0", tkinter.END).strip(),
                    "level": level,
                    "deadline": deadline,
                }
                dialog.destroy()
                self.display()

        def pack_button(text: str, callback) -> None:
            tkinter.Button(
                dialog,
                text=text,
                height=self._height,
                width=self._width,
                command=callback,
            ).pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)

        task = None if idx < 0 else self._data["tasks"][idx]

        dialog = create_window(NAME + " " + self._name + " new")
        dialog.protocol("WM_DELETE_WINDOW", lambda: [dialog.destroy(), self.display()])

        text_title = tkinter.Text(dialog, height=self._height, width=self._width)
        text_title.insert(tkinter.END, "title" if task is None else task["title"])
        text_title.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)

        text_description = tkinter.Text(dialog, height=20, width=self._width)
        text_description.insert(tkinter.END, "description" if task is None else task["text"])
        text_description.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)

        comb_level = tkinter.ttk.Combobox(dialog, width=self._width, state="readonly", justify="center", values=LEVELS)
        comb_level.current(2 if task is None else LEVELS.index(task["level"]))
        comb_level.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.X)

        str_today = format_date(datetime.datetime.now())
        listed_dates = list_date(30)
        if task is None and str_today not in listed_dates:
            listed_dates = [str_today] + listed_dates
        if task is not None and task["deadline"] not in listed_dates:
            listed_dates = [task["deadline"]] + listed_dates
        comb_deadline = tkinter.ttk.Combobox(dialog, justify="center", width=self._width, values=listed_dates)
        comb_deadline.current(listed_dates.index(str_today if task is None else task["deadline"]))
        comb_deadline.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.X)

        if idx < 0:
            pack_button("add", lambda i=0: edit(idx, i))
        else:
            steps = self._get_steps()
            if task["step"] != KEY_HIDDEN:
                i_step = steps.index(task["step"])
                pack_button("||| update |||", lambda i=i_step: edit(idx, i))
                if i_step > 0:
                    pack_button(
                        f"<<< {steps[i_step - 1]} <<<",
                        lambda i=(i_step - 1): edit(idx, i),
                    )
                if i_step + 1 <= len(steps):
                    pack_button(
                        f">>> {(steps + [KEY_HIDDEN])[i_step + 1]} >>>",
                        lambda i=(i_step + 1): edit(idx, i),
                    )
            else:
                pack_button(f"back to {steps[0]}", lambda i=0: edit(idx, i))

    def save(self, path: Optional[str] = None) -> None:
        """
        Save the project conditions.
        """
        with open(self._path if path is None else path, "w", encoding="utf-8") as fs:
            json.dump(self._data, fs, indent=1)

    def backup(self) -> None:
        """
        Back up the project condition with name and time.
        """
        backup_path = self._path + "." + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".back"
        self.save(backup_path)

    def delete(self) -> None:
        """
        Delete the current project. Backup will remain.
        """
        main = create_window(NAME + " " + self._name)
        tkinter.Button(
            main,
            text="delete project",
            height=self._height,
            width=self._width,
            command=lambda: [os.remove(self._path), main.destroy(), list_projects()],
        ).pack(side=tkinter.LEFT)

    def disp_hidden(self) -> None:
        """
        Show the tasks in hidden status.
        """
        main = create_window(NAME + " " + self._name + " hidden")
        main.protocol("WM_DELETE_WINDOW", lambda: [main.destroy(), self.display()])

        canvas = tkinter.Canvas(main, height=600)
        self.bind_canvas(window=main, canvas=canvas)
        scrollbar = tkinter.Scrollbar(main, orient=tkinter.VERTICAL, command=canvas.yview)
        frame_hidden_tasks = tkinter.Frame(canvas)

        for idx, task in self._get_tasks_in_step(KEY_HIDDEN).items():
            tkinter.Button(
                frame_hidden_tasks,
                text=(task["title"] + "\n" + task["deadline"]),
                height=self._height,
                width=self._width,
                command=lambda i=idx: [main.destroy(), self.edit_task(i)],
            ).pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.X)

        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
        canvas.create_window(0, 0, anchor=tkinter.N, window=frame_hidden_tasks)
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox(tkinter.ALL), yscrollcommand=scrollbar.set)
        canvas.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)

    def disp_text(self, disp_updated: bool = True) -> None:
        """
        Show the json file with project content, and save by closing (when the text is valid).
        disp_updated: whether to display and save the updated (or last saved) content.
        """

        def on_close() -> None:
            try:
                data = json.loads(text_field.get("1.0", tkinter.END).strip())
                self._check(data)
                data["tasks"] = {int(k): v for k, v in data["tasks"].items()}
                self._data = data
                self.display()
            except AssertionError as error:
                print(f"data check failed, will just close: {error}")
            finally:
                main.destroy()

        main = create_window(NAME + " " + self._name + (" current" if disp_updated else " saved"))
        main.protocol("WM_DELETE_WINDOW", on_close)

        text_field = tkinter.Text(main, height=20, width=120)
        if disp_updated:
            text_field.insert(tkinter.END, json.dumps(self._data, indent=1))
        else:
            with open(self._path, "r", encoding="utf-8") as fs:
                text_field.insert(tkinter.END, fs.read())
        text_field.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)

    def check_on_close(self) -> None:
        """
        Check whether there is unsaved update; if so, pop up a dialog to save or discard.
        """
        data_curr = json.dumps(self._data, indent=1)
        with open(self._path, "r", encoding="utf-8") as fs:
            data_saved = fs.read()
        if data_curr != data_saved:
            warning = create_window("warning")
            tkinter.Button(
                warning,
                text="save",
                height=self._height,
                width=self._width,
                command=lambda: [self.save(), warning.destroy()],
            ).pack(side=tkinter.TOP)
            tkinter.Button(
                warning,
                text="discard",
                height=self._height,
                width=self._width,
                command=warning.destroy,
            ).pack(side=tkinter.TOP)

    @staticmethod
    def bind_canvas(window: tkinter.Toplevel, canvas: tkinter.Canvas) -> None:
        """
        Make the canvas scrollable with mouse wheel.
        """
        # for Windows
        window.bind_all(
            "<MouseWheel>",
            lambda event: canvas.yview_scroll(1 if event.delta < 0 else -1, "units"),
        )
        # for Linux up-scrolling
        window.bind_all("<Button-4>", lambda _: canvas.yview_scroll(-1, "units"))
        # for Linux down-scrolling
        window.bind_all("<Button-5>", lambda _: canvas.yview_scroll(1, "units"))

    def display(self) -> None:
        """
        Show the kanban.
        """

        def reset() -> None:
            if self._window_main is not None:
                self._window_main.destroy()
                self._window_main = None

        reset()

        self._window_main = create_window(NAME + " " + self._name)
        self._window_main.protocol("WM_DELETE_WINDOW", lambda: [self.check_on_close(), reset()])

        steps = self._get_steps()

        canvas = tkinter.Canvas(self._window_main, width=800, height=600)
        self.bind_canvas(window=self._window_main, canvas=canvas)
        scrollbar = tkinter.Scrollbar(self._window_main, orient=tkinter.VERTICAL, command=canvas.yview)
        frame_cols = tkinter.Frame(canvas)
        frame_util = tkinter.Frame(self._window_main)

        utils = {
            "new": lambda: [reset(), self.edit_task()],
            "save": self.save,
            "backup": self.backup,
            "delete": lambda: [reset(), self.delete()],
            "hidden": lambda: [reset(), self.disp_hidden()],
            "raw": lambda disp=False: self.disp_text(disp_updated=disp),
            "tmp": lambda disp=True: self.disp_text(disp_updated=disp),
        }
        width_util = self._width * len(steps) // len(utils)
        for text, callback in utils.items():
            tkinter.Button(
                frame_util,
                text=text,
                height=self._height,
                width=width_util,
                command=callback,
            ).pack(side=tkinter.LEFT, expand=tkinter.YES, fill=tkinter.X)

        today = parse_date(format_date(datetime.datetime.now()))
        assert today is not None

        for col, step in enumerate(steps):
            tkinter.Label(frame_cols, height=self._height, width=self._width, text=step).grid(
                row=0, rowspan=1, column=col
            )
            row = 1
            for idx, task in self._get_tasks_in_step(step).items():
                background, border = encode_color(task=task, today=today)
                border_frame = tkinter.Frame(frame_cols, background=border)
                tkinter.Button(
                    border_frame,
                    text=(task["title"] + "\n" + task["deadline"]),
                    height=self._height,
                    width=self._width,
                    background=background,
                    command=lambda i=idx: [reset(), self.edit_task(i)],
                ).pack(padx=5, pady=5)
                border_frame.grid(row=row, column=col)
                row += 1

        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        canvas.create_window(0, 0, anchor=tkinter.N, window=frame_cols)
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox(tkinter.ALL), yscrollcommand=scrollbar.set)
        canvas.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)
        frame_util.pack(side=tkinter.BOTTOM, fill=tkinter.X)

    def _check(self, data: dict) -> None:
        """
        Check whether the project content is valid.
        """
        # general
        assert "name" in data and isinstance(data["name"], str) and bool(data["name"]), "name in project not valid"
        assert "steps" in data and isinstance(data["steps"], list) and bool(data["steps"]), "steps in project not valid"
        assert "tasks" in data and isinstance(data["tasks"], dict), "tasks in project not valid"

        tasks = data["tasks"]

        # step
        assert all(
            "step" in task and (task["step"] in data["steps"] or task["step"] == KEY_HIDDEN)
            for _, task in tasks.items()
        ), "tasks have invalid step"
        # title
        assert all("title" in task and bool(task["title"]) for _, task in tasks.items()), "tasks have invalid title"
        # text
        assert all("text" in task and bool(task["text"]) for _, task in tasks.items()), "tasks have invalid text"
        # deadline
        assert all("deadline" in task and parse_date(task["deadline"]) is not None for _, task in tasks.items()), (
            "tasks have invalid deadline"
        )
        # level
        assert all("level" in task and task["level"] in LEVELS for _, task in tasks.items()), "tasks have invalid level"


def init_project() -> None:
    """
    Initialize one project. It will pop out a dialog for defined steps.
    """

    def create() -> None:
        name = text_name.get("1.0", tkinter.END).strip()
        filename = os.path.join(PATH_PROJ, name + EXT)
        assert "\n" not in name, "name cannot contain newline"
        assert not os.path.isfile(filename), "name exists"
        steps = tuple(it.strip() for it in text_steps.get("1.0", tkinter.END).split("\n"))
        steps = tuple(step for step in steps if bool(step) and step != KEY_HIDDEN)

        config = {
            "name": name,
            "steps": steps,
            "tasks": {},
        }
        with open(filename, "w", encoding="utf-8") as fs:
            json.dump(config, fs, indent=1)

        main.destroy()
        list_projects()

    height = BUTTON_HEIGHT
    width = BUTTON_WIDTH * 2

    main = create_window(NAME + " create")

    text_name = tkinter.Text(main, height=height, width=width)
    text_name.insert(tkinter.END, "name_of_the_new_project")
    text_name.pack(side=tkinter.TOP)

    text_steps = tkinter.Text(main, height=height * 5, width=width)
    text_steps.insert(
        tkinter.END,
        "\n".join(("to_start", "in_progress", "in_verification", "finished")),
    )
    text_steps.pack(side=tkinter.TOP)

    tkinter.Button(main, text="create", height=height, width=width, command=create).pack(side=tkinter.TOP)


def list_projects() -> None:
    """
    List the available projects and one button for creating new project.
    """
    height = BUTTON_HEIGHT
    width = BUTTON_WIDTH * 2

    if not os.path.isdir(PATH_PROJ):
        os.mkdir(PATH_PROJ)

    projs = tuple(proj[: -len(EXT)] for proj in os.listdir(PATH_PROJ) if proj.endswith(EXT))

    root = ROOT
    for child in root.winfo_children():
        child.destroy()
    root.title(NAME)

    tkinter.Button(
        root,
        text="create project",
        height=height,
        width=width,
        command=lambda: [init_project()],
    ).pack(side=tkinter.TOP)

    for proj in projs:
        tkinter.Button(
            root,
            text=proj,
            height=height,
            width=width,
            command=lambda name=proj: Project(name=name).display(),
        ).pack(side=tkinter.TOP)

    root.deiconify()


if __name__ == "__main__":
    list_projects()
    ROOT.mainloop()
