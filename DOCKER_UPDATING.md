## Windows Updating

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

## macOS Updating

1. Press <kbd>⌘ Command</kbd> + <kbd>Space</kbd> to open the **Spotlight** menu. Type `Terminal` and then hit <kbd>↵ Return</kbd>
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

## Linux Updating

1. Open the terminal
2. Run these commands in a row:
- `sudo docker stop mgw-app`
- `sudo docker rm mgw-app`
- `sudo docker volume rm mgw-data`
- `sudo docker pull sergree/matchering-web`
3. Finally, run the updated container:
   ```
   sudo docker run -dp 8360:8360 -v mgw-data:/app/data --name mgw-app --restart always sergree/matchering-web
   ```
4. Enjoy your updated **Matchering 2.0** at 🎉 **http://127.0.0.1:8360** 🎉
