# macOS - Matchering 2.0 Docker Image

**[Docker Desktop for Mac]** requires **Apple macOS Mojave 10.14 or newer**. 

1. Download and install **[Docker Desktop for Mac]**. Use the **Docker Desktop** shortcut if it didn't start automatically
2. Wait for **Docker** to load: its menu bar icon will stop flashing. You can simply close the **Login with your Docker ID** window when it appears
3. **IMPORTANT**: Increase the amount of **Memory** used by **Docker** from **2.00 GB** to **4.00 GB**:

   - Open the **Docker Desktop** menu by clicking the **Docker menu bar icon**
   - Select **Preferences**
   - Go to **Resources > Advanced** tab, increase **Memory** to **4.00 GB** and click **Apply & Restart**
   
   ![Docker Memory](https://raw.githubusercontent.com/sergree/matchering/master/images/docker-4gb.png)
   
   *If you don't have **Advanced** tab, that's fine. Just keep going*
4. Wait for **Docker** to load again
5. Press <kbd>⌘ Command</kbd> + <kbd>Space</kbd> to open the **Spotlight** menu. Type `Terminal` and then hit <kbd>↵ Return</kbd>
6. Copy and paste this command into the **Terminal**, then press <kbd>↵ Return</kbd>:
   ```
   docker run -dp 8360:8360 -v mgw-data:/app/data --name mgw-app --restart always sergree/matchering-web
   ```
7. Wait for **Matchering 2.0** to load. It will print `Status: Downloaded newer image...`
8. Enjoy your **Matchering 2.0** at 🎉 **http://127.0.0.1:8360** 🎉 It will also run automatically at startup

### IMPORTANT: Read the [Keep the Privacy] page if you would like to host our web application publicly!

[Docker Desktop for Mac]: https://download.docker.com/mac/stable/Docker.dmg
[Docker Toolbox]: https://docs.docker.com/toolbox/overview/
[Keep the Privacy]: https://github.com/sergree/matchering/wiki/Keep-the-Privacy
