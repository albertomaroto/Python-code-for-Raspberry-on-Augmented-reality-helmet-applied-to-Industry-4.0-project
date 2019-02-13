import curses, time, locale

class interfaz():
        
        screen = None
        
        def iniciar_entorno(self):
                locale.setlocale(locale.LC_ALL,'')
                self.screen = curses.initscr()
                self.screen.refresh()
                
        def cerrar_entorno(self):
                self.screen = curses.endwin()
                
        def escribir(self,y,x,texto,tiempo=None):
                self.screen.move(y,x)
                self.screen.clrtoeol()
                self.screen.addstr(y,x,texto.encode("UTF-8"))
                self.screen.refresh()
                if tiempo is not None:
                        time.sleep(tiempo)
                        self.clear()
                
        def clear(self):
                for i in range (1,16):
                        self.screen.move(i,0)
                        self.screen.clrtoeol()
                self.screen.refresh()

