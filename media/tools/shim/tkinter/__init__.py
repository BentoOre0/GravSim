"""tkinter stand-in - GravSim only uses it for the parameter dialogs,
which never fire in headless capture (params are set directly instead)."""


class Tk:
    def withdraw(self):
        pass

    def destroy(self):
        pass

    def mainloop(self):
        pass
