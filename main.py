import tkinter
import os
import json
import datetime

# Name of the program.
NAME = 'MiKan'
# Extension for the project files.
EXT = '.prj'
# Root path of the projects.
PATH_ROOT = os.path.dirname(os.path.realpath(__file__))
# Path for saving the projects.
PATH_PROJ = os.path.join(PATH_ROOT, '.proj')
# Key for the tasks not to show.
KEY_HIDDEN = 'hidden'
# Allowed levels for tasks
LEVELS = {'critical', 'high', 'normal'}
# Whether a weekday is working day [?, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]
WORKING_DAYS = (None, True, True, True, True, True, False, False)


def parse_date(string: str) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(string, '%Y-%m-%d')
    except:
        return None


def format_date(date: datetime.datetime) -> str:
    try:
        return date.strftime('%Y-%m-%d')
    except:
        return None


def distance_date(start: datetime.datetime, end: datetime.datetime) -> int:
    if start > end:
        return -1
    interval = datetime.timedelta(days=1)
    i = 0
    while start < end:
        start += interval
        i += (1 if WORKING_DAYS[start.isocalendar()[2]] else 0)
    return i


def encode_color(task: dict, today: datetime.datetime) -> str:
    rule = {
        'critical': 'red',
        'high': 'yellow',
    }
    if 'level' in task and task['level'] in rule:
        return rule[task['level']]
    else:
        interval = distance_date(today, parse_date(task['deadline']))
        if interval <= 1:
            return 'red'
        elif interval <= 3:
            return 'yellow'
    return None


class Project(object):
    def __init__(self, name: str) -> None:
        self._name = name
        self._path = os.path.join(PATH_PROJ, name + EXT)
        with open(self._path, 'r') as fs:
            self._data = json.loads(fs.read())
        self._data['tasks'] = {
            int(k): v
            for k, v in self._data['tasks'].items()
        }
        self._check()
        self._height = 3
        self._width = 40

    def get_steps(self) -> list:
        return self._data['steps']

    def get_tasks_in_step(self, step: str) -> list:
        return {
            idx: task
            for idx, task in self._data['tasks'].items()
            if task['step'] == step
        }

    def edit_task(self, idx: int = -1) -> None:
        def edit(idx: int, i_step: int) -> None:
            title = text_title.get('1.0', tkinter.END).strip()
            assert '\n' not in title, 'title cannot contain newline'
            if idx < 0:
                idx = (max(self._data['tasks'].keys()) +
                       1) if bool(self._data['tasks']) else 0
            deadline = text_deadline.get('1.0', tkinter.END).strip()
            level = text_level.get('1.0', tkinter.END).strip()
            if parse_date(deadline) is not None and level in LEVELS:
                step_to_be = (self._data['steps'] + [
                    KEY_HIDDEN,
                ])[i_step]
                self._data['tasks'][idx] = {
                    'step': step_to_be,
                    'title': title,
                    'text': text_description.get('1.0', tkinter.END).strip(),
                    'level': level,
                    'deadline': deadline,
                }
                dialog.destroy()
                self.update_vis()

        task = None if idx < 0 else self._data['tasks'][idx]

        dialog = tkinter.Tk()
        dialog.title(NAME + ' ' + self._name + ' new')

        text_title = tkinter.Text(dialog,
                                  height=self._height,
                                  width=self._width)
        text_title.insert(tkinter.END,
                          'title' if task is None else task['title'])
        text_title.pack(side=tkinter.TOP)

        text_description = tkinter.Text(dialog, height=20, width=self._width)
        text_description.insert(
            tkinter.END, 'description' if task is None else task['text'])
        text_description.pack(side=tkinter.TOP)

        text_level = tkinter.Text(dialog, height=3, width=self._width)
        text_level.insert(tkinter.END,
                          'normal' if task is None else task['level'])
        text_level.pack(side=tkinter.TOP)

        text_deadline = tkinter.Text(dialog,
                                     height=self._height,
                                     width=self._width)
        text_deadline.insert(
            tkinter.END,
            format_date(datetime.datetime.now())
            if task is None else task['deadline'])
        text_deadline.pack(side=tkinter.TOP)

        if idx < 0:
            tkinter.Button(
                dialog,
                text='add',
                height=self._height,
                width=self._width,
                command=lambda i=0: edit(idx, i)).pack(side=tkinter.TOP)
        else:
            steps = self._data['steps']
            if task['step'] != KEY_HIDDEN:
                i_step = steps.index(task['step'])
                tkinter.Button(dialog,
                               text='update',
                               height=self._height,
                               width=self._width,
                               command=lambda i=i_step: edit(idx, i)).pack(
                                   side=tkinter.TOP)
                if i_step > 0:
                    tkinter.Button(
                        dialog,
                        text=steps[i_step - 1],
                        height=self._height,
                        width=self._width,
                        command=lambda i=(i_step - 1): edit(idx, i)).pack(
                            side=tkinter.TOP)
                if i_step + 1 <= len(steps):
                    tkinter.Button(
                        dialog,
                        text=(steps + [
                            KEY_HIDDEN,
                        ])[i_step + 1],
                        height=self._height,
                        width=self._width,
                        command=lambda i=(i_step + 1): edit(idx, i)).pack(
                            side=tkinter.TOP)
            else:
                tkinter.Button(
                    dialog,
                    text=f'back to {steps[0]}',
                    height=self._height,
                    width=self._width,
                    command=lambda i=0: edit(idx, i)).pack(side=tkinter.TOP)

    def save(self, path: str = None) -> None:
        text_config = json.dumps(self._data, indent=' ')
        with open(self._path if path is None else path, 'w') as fs:
            fs.write(text_config)

    def backup(self) -> None:
        self.save(self._path + '.' +
                  datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.back')

    def delete(self) -> None:
        main = tkinter.Tk()
        main.title(NAME + ' ' + self._name)
        tkinter.Button(
            main,
            text='delete project',
            height=self._height,
            width=self._width,
            command=lambda: [os.remove(self._path),
                             main.destroy()]).pack(side=tkinter.LEFT)

    def disp_hidden(self) -> None:
        main = tkinter.Tk()
        main.title(NAME + ' ' + self._name + ' hidden')

        tkinter.Button(
            main,
            text='back',
            height=self._height,
            width=self._width,
            command=lambda: [main.destroy(), self.update_vis()]).pack(
                side=tkinter.TOP)

        for idx, task in self.get_tasks_in_step(KEY_HIDDEN).items():
            tkinter.Button(
                main,
                text=(task['title'] + '\n' + task['deadline']),
                height=self._height,
                width=self._width,
                command=lambda i=idx: [main.destroy(
                ), self.edit_task(i)]).pack(side=tkinter.TOP)

    def disp_raw(self) -> None:
        main = tkinter.Tk()
        main.title(NAME + ' ' + self._name + ' raw')

        text_raw = tkinter.Text(main, height=20, width=120)
        with open(self._path, 'r') as fs:
            text_raw.insert(tkinter.END, fs.read())
        text_raw.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)

    def disp_tmp(self) -> None:
        main = tkinter.Tk()
        main.title(NAME + ' ' + self._name + ' tmp')

        text_raw = tkinter.Text(main, height=20, width=120)
        text_raw.insert(tkinter.END, json.dumps(self._data, indent=' '))
        text_raw.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)

    def update_vis(self) -> None:
        main = tkinter.Tk()
        main.title(NAME + ' ' + self._name)
        frames = []
        frame_cols = tkinter.Frame(main)
        frame_util = tkinter.Frame(main)

        tkinter.Button(
            frame_util,
            text='new',
            height=self._height,
            width=self._width,
            command=lambda: [main.destroy(), self.edit_task()]).pack(
                side=tkinter.LEFT, expand=tkinter.YES, fill=tkinter.BOTH)
        tkinter.Button(frame_util,
                       text='save',
                       height=self._height,
                       width=self._width,
                       command=self.save).pack(side=tkinter.LEFT,
                                               expand=tkinter.YES,
                                               fill=tkinter.BOTH)
        tkinter.Button(frame_util,
                       text='backup',
                       height=self._height,
                       width=self._width,
                       command=self.backup).pack(side=tkinter.LEFT,
                                                 expand=tkinter.YES,
                                                 fill=tkinter.BOTH)
        tkinter.Button(
            frame_util,
            text='delete',
            height=self._height,
            width=self._width,
            command=lambda: [main.destroy(), self.delete()]).pack(
                side=tkinter.LEFT, expand=tkinter.YES, fill=tkinter.BOTH)
        tkinter.Button(frame_util,
                       text='hidden',
                       height=self._height,
                       width=self._width,
                       command=lambda: [main.destroy(
                       ), self.disp_hidden()]).pack(side=tkinter.LEFT,
                                                    expand=tkinter.YES,
                                                    fill=tkinter.BOTH)
        tkinter.Button(frame_util,
                       text='raw',
                       height=self._height,
                       width=self._width,
                       command=self.disp_raw).pack(side=tkinter.LEFT,
                                                   expand=tkinter.YES,
                                                   fill=tkinter.BOTH)
        tkinter.Button(frame_util,
                       text='tmp',
                       height=self._height,
                       width=self._width,
                       command=self.disp_tmp).pack(side=tkinter.LEFT,
                                                   expand=tkinter.YES,
                                                   fill=tkinter.BOTH)

        steps = tuple(step for step in self.get_steps() if step != KEY_HIDDEN)
        today = parse_date(format_date(datetime.datetime.now()))
        for col, step in enumerate(steps):
            tkinter.Label(frame_cols,
                          height=self._height,
                          width=self._width,
                          text=step).grid(row=0, rowspan=1, column=col)
            row = 1
            for idx, task in self.get_tasks_in_step(step).items():
                tkinter.Button(
                    frame_cols,
                    text=(task['title'] + '\n' + task['deadline']),
                    height=self._height,
                    width=self._width,
                    bg=encode_color(task=task, today=today),
                    command=lambda i=idx: [main.destroy(),
                                           self.edit_task(i)]).grid(row=row,
                                                                    column=col)
                row += 1

        frame_cols.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.Y)
        frame_util.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.Y)

    def _check(self) -> None:
        # check general
        assert 'name' in self._data and type(self._data['name']) == str and bool(self._data['name']),\
            'name in project not valid'
        assert 'steps' in self._data and type(self._data['steps']) == list and bool(self._data['steps']),\
            'steps in project not valid'
        assert 'tasks' in self._data and type(self._data['tasks']) == dict,\
            'tasks in project not valid'
        # check tasks
        assert all('step' in task and (task['step'] in self._data['steps'] or task['step'] == KEY_HIDDEN)
            for _, task in self._data['tasks'].items()),\
            'tasks have invalid step'
        assert all('title' in task and bool(task['title']) for _, task in self._data['tasks'].items()),\
            'tasks have invalid title'
        assert all('text' in task and bool(task['text']) for _, task in self._data['tasks'].items()),\
            'tasks have invalid text'
        assert all('deadline' in task and parse_date(task['deadline']) is not None for _, task in self._data['tasks'].items()),\
            'tasks have invalid deadline'
        assert all('level' in task and task['level'] in LEVELS for _, task in self._data['tasks'].items()),\
            'tasks have invalid level'


def start_project(name: str) -> None:
    print("start ", name)
    project = Project(name)
    project.update_vis()


def init_project() -> None:
    def create() -> None:
        name = text_name.get('1.0', tkinter.END).strip()
        filename = os.path.join(PATH_PROJ, name + EXT)
        assert '\n' not in name, 'name cannot contain newline'
        assert not os.path.isfile(filename), 'name exists'
        steps = tuple(it.strip()
                      for it in text_steps.get('1.0', tkinter.END).split('\n'))
        steps = tuple(step for step in steps if bool(step))

        text_config = json.dumps({
            'name': name,
            'steps': steps,
            'tasks': {},
        },
                                 indent=' ')
        with open(filename, 'w') as fs:
            fs.write(text_config)

        main.destroy()
        list_projects()

    height = 3
    width = 80

    main = tkinter.Tk()
    main.title(NAME + ' create')

    text_name = tkinter.Text(main, height=height, width=width)
    text_name.insert(tkinter.END, 'name_of_the_new_project')
    text_name.pack(side=tkinter.TOP)

    text_steps = tkinter.Text(main, height=height * 5, width=width)
    text_steps.insert(
        tkinter.END, '\n'.join(
            ('to_start', 'in_progress', 'in_verification', 'finished')))
    text_steps.pack(side=tkinter.TOP)

    tkinter.Button(main,
                   text='create',
                   height=height,
                   width=width,
                   command=create).pack(side=tkinter.TOP)


def list_projects() -> None:
    height = 3
    width = 80

    if not os.path.isdir(PATH_PROJ):
        os.mkdir(PATH_PROJ)

    projs = tuple(proj[:-len(EXT)] for proj in os.listdir(PATH_PROJ)
                  if proj.endswith(EXT))

    root = tkinter.Tk()
    root.title(NAME)

    tkinter.Button(
        root,
        text='create project',
        height=height,
        width=width,
        command=lambda: [root.destroy(), init_project()]).pack(
            side=tkinter.TOP)
    for proj in projs:
        tkinter.Button(
            root,
            text=proj,
            height=height,
            width=width,
            command=lambda name=proj:
            [root.destroy(), start_project(name=name)]).pack(side=tkinter.TOP)

    tkinter.mainloop()


if __name__ == '__main__':
    list_projects()
