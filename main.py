#!/usr/bin/env python3

import datetime
import json
import os
import tkinter
import tkinter.messagebox
import tkinter.ttk
from collections.abc import Callable
from typing import Any, TypedDict, cast

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
LEVELS: list[str] = ["critical", "high", "normal", "low"]
# Whether a weekday is working day [?, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]
WORKING_DAYS: tuple[bool | None, ...] = (None, True, True, True, True, True, False, False)
# Default height for components.
BUTTON_HEIGHT = 3
# Default width for components.
BUTTON_WIDTH = 40

# Single root window to keep GUI consistent
ROOT = tkinter.Tk()
ROOT.title(NAME)


class Task(TypedDict):
    """Fields stored for one task."""

    step: str
    title: str
    text: str
    level: str
    deadline: str


class ProjectData(TypedDict):
    """Fields stored for one project."""

    name: str
    steps: list[str]
    tasks: dict[int, Task]


def create_window(title: str, parent: tkinter.Misc | None = None) -> tkinter.Toplevel:
    """
    Create a child window and position it relative to its owner.

    Args:
        title: Window title.
        parent: Optional owning window; defaults to the application root.

    Returns:
        The created top-level window.
    """
    owner = ROOT if parent is None else parent
    win = tkinter.Toplevel(owner)
    win.transient(owner)
    win.title(title)

    def position_after_layout() -> None:
        """Center the window over its owner after its requested size is known."""
        if not win.winfo_exists():
            return
        if not isinstance(owner, (tkinter.Tk, tkinter.Toplevel)) or not owner.winfo_exists():
            return
        win.update_idletasks()
        width = win.winfo_width()
        height = win.winfo_height()
        x = owner.winfo_rootx() + max(0, (owner.winfo_width() - width) // 2)
        y = owner.winfo_rooty() + max(0, (owner.winfo_height() - height) // 2)
        win.geometry(f"+{x}+{y}")

    win.after_idle(position_after_layout)
    return win


def parse_date(string: str) -> datetime.datetime | None:
    """
    Parse a date in the strict ``YYYY-MM-DD`` format.

    Args:
        string: Date text to parse.

    Returns:
        The parsed date, or ``None`` if the text is invalid or noncanonical.
    """
    try:
        date = datetime.datetime.strptime(string, "%Y-%m-%d")
        return date if format_date(date) == string else None
    except (TypeError, ValueError):
        return None


def format_date(date: datetime.datetime) -> str:
    """
    Format a date as ``YYYY-MM-DD``.

    Args:
        date: Date value to format.

    Returns:
        The formatted date string.
    """
    return date.strftime("%Y-%m-%d")


def distance_date(start: datetime.datetime, end: datetime.datetime) -> int:
    """
    Count working days from ``start`` up to, but not including, ``end``.

    Args:
        start: Start of the date interval.
        end: End of the date interval.

    Returns:
        The number of working days, or ``-1`` if ``start`` is after ``end``.
    """
    start_date = datetime.date(year=start.year, month=start.month, day=start.day)
    end_date = datetime.date(year=end.year, month=end.month, day=end.day)

    if start_date > end_date:
        return -1

    working = 0
    current = start_date
    while current < end_date:
        if WORKING_DAYS[current.isocalendar().weekday]:
            working += 1
        current += datetime.timedelta(days=1)
    return working


def encode_color(task: Task, today: datetime.datetime) -> tuple[str, str]:
    """
    Choose task background and deadline urgency colors.

    Args:
        task: Task whose importance and deadline determine the colors.
        today: Date used to calculate deadline urgency.

    Returns:
        A pair containing the background color and border color.
    """
    rule = {
        "critical": "#B22222",
        "high": "#FFA500",
        "normal": "#FDF5E6",
        "low": "#9ACD32",
    }
    background = rule[task["level"]]

    deadline_dt = parse_date(task["deadline"])
    interval = 9999 if deadline_dt is None else distance_date(today, deadline_dt)

    if interval <= 1:
        border = "#B22222"
    elif interval <= 3:
        border = "#FFA500"
    else:
        border = background

    return background, border


def list_date(size: int = 30) -> list[str]:
    """
    List upcoming working dates, starting today.

    Args:
        size: Maximum number of dates to return.

    Returns:
        Working dates formatted as ``YYYY-MM-DD``.
    """
    result: list[str] = []
    date = datetime.datetime.now()
    one_day = datetime.timedelta(days=1)
    for _ in range(size):
        if WORKING_DAYS[date.isocalendar()[2]]:
            result.append(format_date(date))
        date += one_day
    return result


def validate_task(title: str, description: str, deadline: str, level: str) -> str | None:
    """
    Validate task fields.

    Args:
        title: Task title.
        description: Task description.
        deadline: Deadline in ``YYYY-MM-DD`` format.
        level: Task importance level.

    Returns:
        An error message if any field is invalid, otherwise ``None``.
    """
    if not title:
        return "A task title is required."
    if not description:
        return "A task description is required."
    if parse_date(deadline) is None:
        return "Deadline must use the YYYY-MM-DD format."
    if level not in LEVELS:
        return "Select a valid task level."
    return None


def pack_dialog_button(
    dialog: tkinter.Toplevel,
    height: int,
    width: int,
    text: str,
    callback: Callable[[], object],
) -> None:
    """Create and pack a standard dialog button.

    Args:
        dialog: Window that will contain the button.
        height: Button height in text units.
        width: Button width in text units.
        text: Button label.
        callback: Function called when the button is activated.
    """
    tkinter.Button(
        dialog,
        text=text,
        height=height,
        width=width,
        command=callback,
    ).pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)


class Project:
    """
    Manage a project's tasks and Tkinter interface.
    """

    def __init__(self, name: str) -> None:
        """Load and validate a project.

        Args:
            name: Project name, excluding the project-file extension.
        """
        self._name = name
        self._path = os.path.join(PATH_PROJ, name + EXT)
        with open(self._path, encoding="utf-8") as fs:
            data: dict[str, Any] = json.load(fs)
        data["tasks"] = {int(key): task for key, task in data["tasks"].items()}
        self._check(data)
        self._data: ProjectData = cast(ProjectData, data)
        self._height = BUTTON_HEIGHT
        self._width = BUTTON_WIDTH
        self._window_main: tkinter.Toplevel | None = None

    def _get_steps(self) -> list[str]:
        """Return the project's workflow steps."""
        return list(self._data["steps"])

    def _get_tasks_in_step(self, step: str) -> dict[int, Task]:
        """Return tasks assigned to a workflow step.

        Args:
            step: Workflow step to filter by.

        Returns:
            Tasks in the requested step, keyed by task ID.
        """
        return {idx: task for idx, task in self._data["tasks"].items() if task["step"] == step}

    def pack_task_buttons(
        self,
        dialog: tkinter.Toplevel,
        idx: int,
        task: Task | None,
        edit: Callable[[int, int], None],
    ) -> None:
        """Add the appropriate task edit and workflow buttons.

        Args:
            dialog: Task editor window.
            idx: Task ID, or a negative value for a new task.
            task: Existing task, or ``None`` when creating one.
            edit: Callback that saves the task at a workflow-step index.
        """
        if task is None:
            pack_dialog_button(dialog, self._height, self._width, "add", lambda i=0: edit(idx, i))
            return

        steps = self._get_steps()
        if task["step"] == KEY_HIDDEN:
            pack_dialog_button(dialog, self._height, self._width, f"back to {steps[0]}", lambda i=0: edit(idx, i))
            return

        i_step = steps.index(task["step"])
        pack_dialog_button(dialog, self._height, self._width, "||| update |||", lambda i=i_step: edit(idx, i))
        if i_step > 0:
            pack_dialog_button(
                dialog,
                self._height,
                self._width,
                f"<<< {steps[i_step - 1]} <<<",
                lambda i=i_step - 1: edit(idx, i),
            )
        if i_step + 1 <= len(steps):
            pack_dialog_button(
                dialog,
                self._height,
                self._width,
                f">>> {(steps + [KEY_HIDDEN])[i_step + 1]} >>>",
                lambda i=i_step + 1: edit(idx, i),
            )

    def edit_task(self, idx: int = -1) -> None:
        """Open a dialog to create or edit a task.

        Args:
            idx: Task ID to edit, or a negative value to create a task.
        """

        def edit(idx_inner: int, i_step: int) -> None:
            """Validate and save the task at the selected workflow step."""
            title = text_title.get("1.0", tkinter.END).strip()
            description = text_description.get("1.0", tkinter.END).strip()
            deadline = comb_deadline.get()
            level = comb_level.get()
            error = validate_task(title, description, deadline, level)
            if error is not None:
                tkinter.messagebox.showerror(NAME, error)
                return
            if idx_inner < 0:
                idx_inner = (max(self._data["tasks"].keys()) + 1) if bool(self._data["tasks"]) else 0
            step_to_be = (self._get_steps() + [KEY_HIDDEN])[i_step]
            task_data: Task = {
                "step": step_to_be,
                "title": title,
                "text": description,
                "level": level,
                "deadline": deadline,
            }
            self._data["tasks"][idx_inner] = task_data
            dialog.destroy()
            self.display()

        task = None if idx < 0 else self._data["tasks"][idx]

        dialog = create_window(NAME + " " + self._name + " new", parent=self._window_main)
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

        self.pack_task_buttons(dialog, idx, task, edit)

    def save(self, path: str | None = None) -> None:
        """Save project data to disk.

        Args:
            path: Optional alternate destination path.
        """
        with open(self._path if path is None else path, "w", encoding="utf-8") as fs:
            json.dump(self._data, fs, indent=1)

    def backup(self) -> None:
        """Write a timestamped backup of the project."""
        backup_path = self._path + "." + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".back"
        self.save(backup_path)

    def delete(self) -> None:
        """Prompt to delete the project while retaining its backups."""
        main = create_window(NAME + " " + self._name, parent=self._window_main)

        def delete_project() -> None:
            """Delete the project after user confirmation."""
            if tkinter.messagebox.askyesno(NAME, f"Delete project '{self._name}'?"):
                os.remove(self._path)
                main.destroy()
                if self._window_main is not None:
                    self._window_main.destroy()
                    self._window_main = None
                list_projects()

        tkinter.Button(
            main,
            text="delete project",
            height=self._height,
            width=self._width,
            command=delete_project,
        ).pack(side=tkinter.LEFT)

    def disp_hidden(self) -> None:
        """Show tasks assigned to the hidden workflow step."""
        main = create_window(NAME + " " + self._name + " hidden", parent=self._window_main)
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
        """Display project JSON and apply valid edits when the window closes.

        Args:
            disp_updated: Whether to show in-memory data instead of saved data.
        """

        def on_close() -> None:
            """Validate and apply edited project JSON before closing."""
            try:
                data: dict[str, Any] = json.loads(text_field.get("1.0", tkinter.END).strip())
                self._check(data)
                data["tasks"] = {int(k): v for k, v in data["tasks"].items()}
                self._data = cast(ProjectData, data)
                self.display()
            except (json.JSONDecodeError, AssertionError, KeyError, ValueError, TypeError) as error:
                tkinter.messagebox.showerror(NAME, f"Invalid project data:\n{error}")
            finally:
                main.destroy()

        main = create_window(
            NAME + " " + self._name + (" current" if disp_updated else " saved"),
            parent=self._window_main,
        )
        main.protocol("WM_DELETE_WINDOW", on_close)

        text_field = tkinter.Text(main, height=20, width=120)
        if disp_updated:
            text_field.insert(tkinter.END, json.dumps(self._data, indent=1))
        else:
            with open(self._path, encoding="utf-8") as fs:
                text_field.insert(tkinter.END, fs.read())
        text_field.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)

    def check_on_close(self) -> None:
        """Prompt to save or discard changes when the project has unsaved data."""
        data_curr = json.dumps(self._data, indent=1)
        with open(self._path, encoding="utf-8") as fs:
            data_saved = fs.read()
        if data_curr != data_saved:
            warning = create_window("warning", parent=self._window_main)
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
        """Bind platform-specific mouse-wheel events to a canvas.

        Args:
            window: Window that receives the wheel events.
            canvas: Canvas to scroll.
        """

        def on_mousewheel(event: tkinter.Event) -> None:
            """Scroll according to the Windows/macOS mouse-wheel delta."""
            canvas.yview_scroll(1 if event.delta < 0 else -1, "units")

        def on_scroll_up(_event: tkinter.Event) -> None:
            """Scroll up for Linux wheel events."""
            canvas.yview_scroll(-1, "units")

        def on_scroll_down(_event: tkinter.Event) -> None:
            """Scroll down for Linux wheel events."""
            canvas.yview_scroll(1, "units")

        window.bind("<MouseWheel>", on_mousewheel)
        window.bind("<Button-4>", on_scroll_up)
        window.bind("<Button-5>", on_scroll_down)

    def display(self) -> None:
        """Display or refresh the project board in its existing window."""

        def reset() -> None:
            """Destroy the project's main window and clear its reference."""
            if self._window_main is not None:
                self._window_main.destroy()
                self._window_main = None

        if self._window_main is not None and self._window_main.winfo_exists():
            geometry = self._window_main.geometry()
            for child in self._window_main.winfo_children():
                child.destroy()
            self._window_main.title(NAME + " " + self._name)
            if geometry:
                self._window_main.geometry(geometry)
        else:
            self._window_main = create_window(NAME + " " + self._name)

        self._window_main.protocol("WM_DELETE_WINDOW", lambda: [self.check_on_close(), reset()])

        steps = self._get_steps()

        canvas = tkinter.Canvas(self._window_main, width=800, height=600)
        self.bind_canvas(window=self._window_main, canvas=canvas)
        scrollbar = tkinter.Scrollbar(self._window_main, orient=tkinter.VERTICAL, command=canvas.yview)
        frame_cols = tkinter.Frame(canvas)
        frame_util = tkinter.Frame(self._window_main)

        utils = {
            "new": self.edit_task,
            "save": self.save,
            "backup": self.backup,
            "delete": self.delete,
            "hidden": self.disp_hidden,
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
                    command=lambda i=idx: self.edit_task(i),
                ).pack(padx=5, pady=5)
                border_frame.grid(row=row, column=col)
                row += 1

        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        canvas.create_window(0, 0, anchor=tkinter.N, window=frame_cols)
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox(tkinter.ALL), yscrollcommand=scrollbar.set)
        canvas.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)
        frame_util.pack(side=tkinter.BOTTOM, fill=tkinter.X)

    def _check(self, data: dict[str, Any]) -> None:
        """Validate project data loaded from JSON.

        Args:
            data: Project data to validate.

        Raises:
            AssertionError: If any required project or task field is invalid.
        """
        # general
        assert "name" in data and isinstance(data["name"], str) and bool(data["name"]), "name in project not valid"
        assert "steps" in data and isinstance(data["steps"], list) and bool(data["steps"]), "steps in project not valid"
        assert "tasks" in data and isinstance(data["tasks"], dict), "tasks in project not valid"

        tasks = data["tasks"]
        assert all(isinstance(task, dict) for task in tasks.values()), "tasks must be objects"

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
    """Open the dialog for creating a project and defining its workflow."""

    def create() -> None:
        """Validate the form and create its project file."""
        name = text_name.get("1.0", tkinter.END).strip()
        if not name or "/" in name or "\\" in name:
            tkinter.messagebox.showerror(NAME, "Project name must be non-empty and cannot contain path separators.")
            return
        filename = os.path.join(PATH_PROJ, name + EXT)
        if os.path.isfile(filename):
            tkinter.messagebox.showerror(NAME, "A project with that name already exists.")
            return
        steps = tuple(it.strip() for it in text_steps.get("1.0", tkinter.END).split("\n"))
        steps = tuple(dict.fromkeys(step for step in steps if step and step != KEY_HIDDEN))
        if not steps:
            tkinter.messagebox.showerror(NAME, "Define at least one workflow step.")
            return
        if len(steps) > 20:
            tkinter.messagebox.showerror(NAME, "A project can contain at most 20 workflow steps.")
            return

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
    """Show available projects and the project-creation button."""
    height = BUTTON_HEIGHT
    width = BUTTON_WIDTH * 2

    if not os.path.isdir(PATH_PROJ):
        os.mkdir(PATH_PROJ)

    projs = sorted(
        (proj[: -len(EXT)] for proj in os.listdir(PATH_PROJ) if proj.endswith(EXT)),
        key=str.casefold,
    )

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
