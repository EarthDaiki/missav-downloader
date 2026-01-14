from missav import Missav

class Example:
    def __init__(self):
        self.missav = Missav()
    
    def run(self, url, path):
        self.missav.run(url, path)


if __name__ == '__main__':
    app = Example()
    app.run('https://missav.ws/ja/hoi-374', r'D:\DaikiVideos\missav')
    