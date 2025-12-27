# MiKan — A Lightweight Personal Kanban Board

MiKan is a simple, local, GUI‑based personal Kanban tool built with Python and Tkinter.
It helps you organize tasks visually, track progress across customizable steps, and manage deadlines with intuitive color cues.

---

## Features

### Customizable workflow

- **Define steps:** Create your own workflow stages (for example: `to_start → in_progress → in_verification → finished`).
- **Move tasks:** Shift tasks between steps with a single click.
- **Hide tasks:** Move finished or inactive tasks into a hidden state and restore them later.

### Task editing dialog

Each task includes:

- **Title**
- **Description**
- **Level:** One of `critical`, `high`, `normal`, `low`
- **Deadline:** In the format `YYYY-MM-DD`

**Color logic:**

- **Background color:** Indicates importance (based on level).
- **Border color:** Indicates urgency (based on how close the deadline is).

### Project utilities

The bottom toolbar provides quick access to common actions:

- **new:** Create a new task.
- **save:** Save the current project.
- **backup:** Save a timestamped backup of the project file.
- **delete:** Delete the project file (backups remain).
- **hidden:** Show tasks that are in the hidden step.
- **raw:** View the project as it is saved on disk (JSON).
- **tmp:** View the current in‑memory project state (JSON).

---

## Screenshots

### Main window

![Main Window](https://github.com/t-lou/MiKan/raw/master/screenshots/window_main.png)

### Task editing dialog

![Task Dialog](https://github.com/t-lou/MiKan/raw/master/screenshots/dialog_task.png)

---

## Getting started

### Requirements

- Python 3.x
- Tkinter (included with most standard Python installations)

### Running the application

From the project directory, run:

```bash
python main.py
```

### Creating a project

1. Launch the program.
2. Click **create project**.
3. Enter a project name.
4. Define your workflow steps (one per line).
5. Start adding tasks to your new board.

---

## Project file format

Each project is stored as a JSON file under the `.proj/` directory.

Example:

```json
{
  "name": "example",
  "steps": ["to_start", "in_progress", "finished"],
  "tasks": {
    "0": {
      "step": "to_start",
      "title": "Example task",
      "text": "Description",
      "level": "normal",
      "deadline": "2025-01-01"
    }
  }
}
```

### Notes

- Hidden tasks use a special step named `"hidden"`.
- Deadlines must follow the `YYYY-MM-DD` format.
- Everything is stored locally; there is no network or cloud component.
