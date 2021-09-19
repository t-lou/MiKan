import tkinter
import tkinter.ttk
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
LEVELS = ['critical', 'high', 'normal', 'low']
# Whether a weekday is working day [?, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday]
WORKING_DAYS = (None, True, True, True, True, True, False, False)
# Default height for components.
BUTTON_HEIGHT = 3
# Default width for components.
BUTTON_WIDTH = 40


def parse_date(string: str) -> datetime.datetime:
    '''
    Parse one date written as "YYYY-MM-DD", such as "1992-01-15".
    Parameters:
        string: the string with date information.
    Output:
        The parsed date. If the format or content is not right, like "2020.02.30", None will be returned.
    '''
    try:
        return datetime.datetime.strptime(string, '%Y-%m-%d')
    except:
        return None


def format_date(date: datetime.datetime) -> str:
    '''
    Format one date as "YYYY-MM-DD", such as "1992-01-15".
    Parameters:
        date: the date to pack. The hour and minutes will be discarded.
    Output:
        The formatted string.
    '''
    return date.strftime('%Y-%m-%d')


def distance_date(start: datetime.datetime, end: datetime.datetime) -> int:
    '''
    Count the number of working days between two dates.
    Parameters:
        start: the starting date.
        end: the ending date.
    Output:
        Number of days in between. If start is after end, -1 will returned.
    '''
    start = datetime.datetime(year=start.year,
                              month=start.month,
                              day=start.day)
    end = datetime.datetime(year=end.year, month=end.month, day=end.day)
    if start > end:
        return -1
    interval = datetime.timedelta(days=1)
    i = 0
    while start < end:
        start += interval
        i += (1 if WORKING_DAYS[start.isocalendar()[2]] else 0)
    return i


def encode_color(task: dict, today: datetime.datetime) -> tuple:
    '''
    Decide the color of one task.
    Parameters:
        task: the task information.
        today: the date of today.
    Output:
        (background color, border color):
        background color shows how important the task is;
        border color shows how urgend the task it.
    '''
    rule = {
        'critical': '#B22222',
        'high': '#FFA500',
        'normal': '#FDF5E6',
        'low': '#9ACD32',
    }
    background = rule[task['level']]

    interval = distance_date(today, parse_date(task['deadline']))
    if interval <= 1:
        border = '#B22222'
    elif interval <= 3:
        border = '#FFA500'
    else:
        border = background

    return background, border


def list_date(size: int = 30) -> list:
    '''
    List the following dates.
    Parameters:
        size: how many dates to list.
    Output:
        A list of strings containing the following dates since today.
    '''
    result = []
    date = datetime.datetime.now()
    one_day = datetime.timedelta(days=1)
    for i in range(size):
        if WORKING_DAYS[date.isocalendar()[2]]:
            result.append(format_date(date))
        date += one_day
    return result


class Project(object):
    '''
    The management of tasks with GUI.
    '''
    def __init__(self, name: str) -> None:
        '''
        Start the project with given name. The content must be already initialized.
        Parameters:
            name: name of the project file.
        '''
        self._name = name
        self._path = os.path.join(PATH_PROJ, name + EXT)
        with open(self._path, 'r') as fs:
            self._data = json.loads(fs.read())
        self._data['tasks'] = {
            int(k): v
            for k, v in self._data['tasks'].items()
        }
        self._check(self._data)
        self._height = BUTTON_HEIGHT
        self._width = BUTTON_WIDTH
        self._window_main = None

    def _get_steps(self) -> list:
        '''
        Get the defined steps in project.
        Output:
            The list of defined steps.
        '''
        return self._data['steps']

    def _get_tasks_in_step(self, step: str) -> dict:
        '''
        Get the tasks which are in the given step.
        Parameters:
            step: name of expected step.
        Output:
            Indexed tasks in the given step.
        '''
        return {
            idx: task
            for idx, task in self._data['tasks'].items()
            if task['step'] == step
        }

    def edit_task(self, idx: int = -1) -> None:
        '''
        Start a dialog for editing the task.
        Parameters:
            idx: the index of the task. If it is negative, the task will be initialized.
        '''
        def edit(idx: int, i_step: int) -> None:
            title = text_title.get('1.0', tkinter.END).strip()
            assert '\n' not in title, 'title cannot contain newline'
            if idx < 0:
                idx = (max(self._data['tasks'].keys()) +
                       1) if bool(self._data['tasks']) else 0
            deadline = comb_deadline.get()
            level = comb_level.get()
            if parse_date(deadline) is not None and level in LEVELS:
                step_to_be = (self._get_steps() + [
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
                self.display()

        def pack_button(text: str, callback) -> None:
            tkinter.Button(dialog,
                           text=text,
                           height=self._height,
                           width=self._width,
                           command=callback).pack(side=tkinter.TOP,
                                                  expand=tkinter.YES,
                                                  fill=tkinter.BOTH)

        task = None if idx < 0 else self._data['tasks'][idx]

        dialog = tkinter.Tk()
        dialog.title(NAME + ' ' + self._name + ' new')
        dialog.protocol(
            'WM_DELETE_WINDOW',
            lambda: [dialog.destroy(), self.display()])

        text_title = tkinter.Text(dialog,
                                  height=self._height,
                                  width=self._width)
        text_title.insert(tkinter.END,
                          'title' if task is None else task['title'])
        text_title.pack(side=tkinter.TOP,
                        expand=tkinter.YES,
                        fill=tkinter.BOTH)

        text_description = tkinter.Text(dialog, height=20, width=self._width)
        text_description.insert(
            tkinter.END, 'description' if task is None else task['text'])
        text_description.pack(side=tkinter.TOP,
                              expand=tkinter.YES,
                              fill=tkinter.BOTH)

        comb_level = tkinter.ttk.Combobox(dialog,
                                          width=self._width,
                                          state='readonly',
                                          justify='center',
                                          values=LEVELS)
        comb_level.current(2 if task is None else LEVELS.index(task['level']))
        comb_level.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.X)

        str_today = format_date(datetime.datetime.now())
        listed_dates = list_date(30)
        if task is None and str_today not in listed_dates:
            listed_dates = [str_today] + listed_dates
        if task is not None and task['deadline'] not in listed_dates:
            listed_dates = [task['deadline']] + listed_dates
        comb_deadline = tkinter.ttk.Combobox(dialog,
                                             justify='center',
                                             width=self._width,
                                             values=listed_dates)
        comb_deadline.current(
            listed_dates.index(
                str_today if task is None else task['deadline']))
        comb_deadline.pack(side=tkinter.TOP,
                           expand=tkinter.YES,
                           fill=tkinter.X)

        if idx < 0:
            pack_button('add', lambda i=0: edit(idx, i))
        else:
            steps = self._get_steps()
            if task['step'] != KEY_HIDDEN:
                i_step = steps.index(task['step'])
                pack_button('||| update |||', lambda i=i_step: edit(idx, i))
                if i_step > 0:
                    pack_button(f'<<< {steps[i_step - 1]} <<<',
                                lambda i=(i_step - 1): edit(idx, i))
                if i_step + 1 <= len(steps):
                    pack_button(
                        f'>>> {(steps + [KEY_HIDDEN])[i_step + 1]} >>>',
                        lambda i=(i_step + 1): edit(idx, i))
            else:
                pack_button(f'back to {steps[0]}', lambda i=0: edit(idx, i))

    def save(self, path: str = None) -> None:
        '''
        Save the project conditions.
        Parameters:
            path: the path to save project in json.
        '''
        text_config = json.dumps(self._data, indent=' ')
        with open(self._path if path is None else path, 'w') as fs:
            fs.write(text_config)

    def backup(self) -> None:
        '''
        Back up the project condition with name and time.
        '''
        self.save(self._path + '.' +
                  datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.back')

    def delete(self) -> None:
        '''
        Delete the current project. Backup will remain.
        '''
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
        '''
        Show the tasks in hidden status.
        '''
        main = tkinter.Tk()
        main.title(NAME + ' ' + self._name + ' hidden')
        main.protocol('WM_DELETE_WINDOW',
                      lambda: [main.destroy(), self.display()])

        canvas = tkinter.Canvas(main, height=600)
        self.bind_canvas(window=main, canvas=canvas)
        scrollbar = tkinter.Scrollbar(main,
                                      orient=tkinter.VERTICAL,
                                      command=canvas.yview)
        frame_hidden_tasks = tkinter.Frame(canvas)

        for idx, task in self._get_tasks_in_step(KEY_HIDDEN).items():
            tkinter.Button(frame_hidden_tasks,
                           text=(task['title'] + '\n' + task['deadline']),
                           height=self._height,
                           width=self._width,
                           command=lambda i=idx:
                           [main.destroy(), self.edit_task(i)]).pack(
                               side=tkinter.TOP,
                               expand=tkinter.YES,
                               fill=tkinter.X)

        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.BOTH)
        canvas.create_window(0, 0, anchor=tkinter.N, window=frame_hidden_tasks)
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox(tkinter.ALL),
                         yscrollcommand=scrollbar.set)
        canvas.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)

    def disp_text(self, disp_updated: bool = True) -> None:
        '''
        Show the json file with project content, and save by closing (when the text is valid).
        Parameters:
            disp_updated: whether to display and save the updated (or last saved) content.
        '''
        def on_close():
            try:
                data = json.loads(text_field.get('1.0', tkinter.END).strip())
                self._check(data)  # assert breaks and it will not continue
                self._data = data
                self.display()
            except:
                pass
            main.destroy()

        main = tkinter.Tk()
        main.title(NAME + ' ' + self._name +
                   (' current' if disp_updated else ' saved'))
        main.protocol('WM_DELETE_WINDOW', on_close)

        text_field = tkinter.Text(main, height=20, width=120)
        if disp_updated:
            text_field.insert(tkinter.END, json.dumps(self._data, indent=' '))
        else:
            with open(self._path, 'r') as fs:
                text_field.insert(tkinter.END, fs.read())
        text_field.pack(side=tkinter.TOP,
                        expand=tkinter.YES,
                        fill=tkinter.BOTH)

    def check_on_close(self) -> None:
        '''
        Check whether there is unsaved update; if so, pop up a dialog to save or discard.
        '''
        data_curr = json.dumps(self._data, indent=' ')
        with open(self._path, 'r') as fs:
            data_saved = fs.read()
        if data_curr != data_saved:
            warning = tkinter.Tk()
            warning.title('warning')
            tkinter.Button(
                warning,
                text='save',
                height=self._height,
                width=self._width,
                command=lambda: [self.save(), warning.destroy()]).pack(
                    side=tkinter.TOP)
            tkinter.Button(warning,
                           text='discard',
                           height=self._height,
                           width=self._width,
                           command=warning.destroy).pack(side=tkinter.TOP)

    @staticmethod
    def bind_canvas(window: tkinter.Tk, canvas: tkinter.Canvas) -> None:
        '''
        Make the canvas scrollbar with mouse wheel.
        Parameters:
            window: The window where the canvas is.
            canvas: The canvas where scrollbar content is.
        '''
        # for windows, in testing
        window.bind_all(
            "<MouseWheel>", lambda event: canvas.yview_scroll(
                1 if event.delta < 0 else -1, 'units'))
        # for linux up-scrolling
        window.bind_all("<Button-4>",
                        lambda _: canvas.yview_scroll(-1, 'units'))
        # for linux down-scrolling
        window.bind_all("<Button-5>",
                        lambda _: canvas.yview_scroll(1, 'units'))

    def display(self) -> None:
        '''
        Show the kanban.
        '''
        def reset():
            if self._window_main is not None:
                self._window_main.destroy()
                self._window_main = None

        reset()

        self._window_main = tkinter.Tk()
        self._window_main.title(NAME + ' ' + self._name)
        self._window_main.protocol(
            'WM_DELETE_WINDOW',
            lambda: [self.check_on_close(), reset()])

        steps = self._get_steps()

        canvas = tkinter.Canvas(self._window_main, width=800, height=600)
        self.bind_canvas(window=self._window_main, canvas=canvas)
        scrollbar = tkinter.Scrollbar(self._window_main,
                                      orient=tkinter.VERTICAL,
                                      command=canvas.yview)
        frame_cols = tkinter.Frame(canvas)
        frame_util = tkinter.Frame(self._window_main)

        utils = {
            'new': lambda: [reset(), self.edit_task()],
            'save': self.save,
            'backup': self.backup,
            'delete': lambda: [reset(), self.delete()],
            'hidden': lambda: [reset(), self.disp_hidden()],
            'raw': lambda disp=False: self.disp_text(disp_updated=disp),
            'tmp': lambda disp=True: self.disp_text(disp_updated=disp),
        }
        width_util = self._width * len(steps) // len(utils)
        for text, callback in utils.items():
            tkinter.Button(frame_util,
                           text=text,
                           height=self._height,
                           width=width_util,
                           command=callback).pack(side=tkinter.LEFT,
                                                  expand=tkinter.YES,
                                                  fill=tkinter.X)

        today = parse_date(format_date(datetime.datetime.now()))
        for col, step in enumerate(steps):
            tkinter.Label(frame_cols,
                          height=self._height,
                          width=self._width,
                          text=step).grid(row=0, rowspan=1, column=col)
            row = 1
            for idx, task in self._get_tasks_in_step(step).items():
                background, border = encode_color(task=task, today=today)
                border = tkinter.Frame(frame_cols, background=border)
                tkinter.Button(
                    border,
                    text=(task['title'] + '\n' + task['deadline']),
                    height=self._height,
                    width=self._width,
                    background=background,
                    command=lambda i=idx: [reset(), self.edit_task(i)]).pack(
                        padx=5, pady=5)
                border.grid(row=row, column=col)
                row += 1

        scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        canvas.create_window(0, 0, anchor=tkinter.N, window=frame_cols)
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox(tkinter.ALL),
                         yscrollcommand=scrollbar.set)
        canvas.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.BOTH)
        # frame_cols.pack(side=tkinter.TOP, expand=tkinter.YES, fill=tkinter.Y)
        frame_util.pack(side=tkinter.BOTTOM, fill=tkinter.X)

    def _check(self, data: dict) -> None:
        '''
        Check whether the project content is valid.
        Parameters:
            data: the content (in dict) of project to check.
        '''
        # check general
        assert 'name' in data and type(data['name']) == str and bool(data['name']),\
            'name in project not valid'
        assert 'steps' in data and type(data['steps']) == list and bool(data['steps']),\
            'steps in project not valid'
        assert 'tasks' in data and type(data['tasks']) == dict,\
            'tasks in project not valid'
        # check tasks
        assert all('step' in task and (task['step'] in data['steps'] or task['step'] == KEY_HIDDEN)
            for _, task in data['tasks'].items()),\
            'tasks have invalid step'
        assert all('title' in task and bool(task['title']) for _, task in data['tasks'].items()),\
            'tasks have invalid title'
        assert all('text' in task and bool(task['text']) for _, task in data['tasks'].items()),\
            'tasks have invalid text'
        assert all('deadline' in task and parse_date(task['deadline']) is not None for _, task in data['tasks'].items()),\
            'tasks have invalid deadline'
        assert all('level' in task and task['level'] in LEVELS for _, task in data['tasks'].items()),\
            'tasks have invalid level'


def init_project() -> None:
    '''
    Initialize one project. It will pop out a dialog for defined steps.
    '''
    def create() -> None:
        name = text_name.get('1.0', tkinter.END).strip()
        filename = os.path.join(PATH_PROJ, name + EXT)
        assert '\n' not in name, 'name cannot contain newline'
        assert not os.path.isfile(filename), 'name exists'
        steps = tuple(it.strip()
                      for it in text_steps.get('1.0', tkinter.END).split('\n'))
        steps = tuple(step for step in steps
                      if bool(step) and step != KEY_HIDDEN)

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

    height = BUTTON_HEIGHT
    width = BUTTON_WIDTH * 2

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
    '''
    List the available projects and one button for creating new project.
    '''
    height = BUTTON_HEIGHT
    width = BUTTON_WIDTH * 2

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
            [root.destroy(), Project(name=name).display()]).pack(
                side=tkinter.TOP)

    tkinter.mainloop()


if __name__ == '__main__':
    list_projects()
