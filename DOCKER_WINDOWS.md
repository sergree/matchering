# Windows - Matchering 2.0 Docker Image

**[Docker Desktop for Windows]** requires **Microsoft Windows 10 64-bit: Pro, Enterprise, or Education**. 

###### For previous versions get **[Docker Toolbox]**.

1. Download and install **[Docker Desktop for Windows]**. Use the **Docker Desktop** shortcut if it didn't start automatically
2. Wait for **Docker** to load: its taskbar icon will stop flashing. You can simply close the **Login with your Docker ID** window when it appears
3. **IMPORTANT**: Increase the amount of **Memory** used by **Docker** from **2.00 GB** to **4.00 GB**:

   - Open the **Docker Desktop** menu by clicking the **Docker taskbar icon**
   - Select **Settings**
   - Go to **Resources > Advanced** tab, increase **Memory** to **4.00 GB** and click **Apply & Restart**
   
   ![Docker Memory](https://raw.githubusercontent.com/sergree/matchering/master/images/docker-4gb.png)
4. Wait for **Docker** to load again
5. Press <kbd>❖ Windows</kbd> + <kbd>R</kbd> to open the **Run** dialog box. Type `cmd` and then hit <kbd>↵ Enter</kbd>
6. Copy and paste this command into the **Command Prompt**, then press <kbd>↵ Enter</kbd>:
```
docker run -dp 8360:8360 -v mgw-data:/app/data --name mgw-app --restart always sergree/matchering-web
```
7. Wait for **Matchering 2.0** to load. It will print `Status: Downloaded newer image...`
8. Enjoy your **Matchering 2.0** at 🎉 **http://127.0.0.1:8360** 🎉 It will also run automatically at startup

If you have any problems, watch the video:

[![Video Guide (Windows)](http://img.youtube.com/vi/rVv23yXkW9g/0.jpg)](http://www.youtube.com/watch?v=rVv23yXkW9g "Matchering 2.0 - Installation (Windows)")

### IMPORTANT: Read the [Keep the Privacy] page if you would like to host our web application publicly!

## Updating

1. Press <kbd>❖ Windows</kbd> + <kbd>R</kbd> to open the **Run** dialog box. Type `cmd` and then hit <kbd>↵ Enter</kbd>
2. Run these commands in a row:
- `docker stop mgw-app`
- `docker rm mgw-app`
- `docker volume rm mgw-data`
- `docker pull sergree/matchering-web`
3. Finally, run the updated container:
```
docker run -dp 8360:8360 -v mgw-data:/app/data --name mgw-app --restart always sergree/matchering-web
```
4. Enjoy your updated **Matchering 2.0** at 🎉 **http://127.0.0.1:8360** 🎉

[Docker Desktop for Windows]: https://download.docker.com/win/stable/Docker%20Desktop%20Installer.exe
[Docker Toolbox]: https://docs.docker.com/toolbox/overview/
[Keep the Privacy]: https://github.com/sergree/matchering/wiki/Keep-the-Privacy
