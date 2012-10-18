from handlers import SuperHandler

class SimpleChartHandler(SuperHandler):
    def get(self):
        datax = range(10)
        datay = [elem ** 2 for elem in datax]
        
        self.render('simplechart.html', datax = datax, datay = datay)