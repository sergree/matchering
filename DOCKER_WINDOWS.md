# Windows - Matchering 2.0 Docker Image

**[Docker Desktop for Windows]** requires **Microsoft Windows 10 64-bit: Pro, Enterprise, Education, or Home**. 

1. Download and install **[Docker Desktop for Windows]**

   ![Win Step 1](https://raw.githubusercontent.com/sergree/matchering/master/images/win_step_1.png)

   ![Win Step 2](https://raw.githubusercontent.com/sergree/matchering/master/images/win_step_2.png)

   *Your system may be restarted after the installation*

2. Use the **Docker Desktop** shortcut if it didn't start automatically

   ![Win Step 3](https://raw.githubusercontent.com/sergree/matchering/master/images/win_step_3.png)

3. If you get this error, you should enable **[hardware virtualization]**

   ![Win Step 4](https://raw.githubusercontent.com/sergree/matchering/master/images/win_step_4.png)

4. If you get this message, you should install **[WSL 2]**. Click **Restart** next

   ![Win Step 5](https://raw.githubusercontent.com/sergree/matchering/master/images/win_step_5.png)

5. Just close these 2 windows as they appear

   ![Win Step 6](https://raw.githubusercontent.com/sergree/matchering/master/images/win_step_6.png)

6. Wait for **Docker** to load: its taskbar icon will stop flashing. You should get this notification

   ![Win Step 7](https://raw.githubusercontent.com/sergree/matchering/master/images/win_step_7.png)

7. Press <kbd>❖ Windows</kbd> + <kbd>R</kbd> to open the **Run** dialog box. Type `cmd` and then hit <kbd>↵ Enter</kbd>

   ![Win Step 8](https://raw.githubusercontent.com/sergree/matchering/master/images/win_step_8.png)

8. Copy and paste this command into the **Command Prompt**, then press <kbd>↵ Enter</kbd>:
   ```
   docker run -dp 8360:8360 -v mgw-data:/app/data --name mgw-app --restart always sergree/matchering-web
   ```

   ![Win Step 9](https://raw.githubusercontent.com/sergree/matchering/master/images/win_step_9.png)

9. Wait for **Matchering 2.0** to load. It will print `Status: Downloaded newer image...`

   ![Win Step 10](https://raw.githubusercontent.com/sergree/matchering/master/images/win_step_10.png)

10. Enjoy your **Matchering 2.0** at 🎉 **http://127.0.0.1:8360** 🎉 It will also run automatically at startup

    ![Win Step 11](https://raw.githubusercontent.com/sergree/matchering/master/images/win_step_11.png)

### IMPORTANT: Read the [Keep the Privacy] page if you would like to host our web application publicly!

[Docker Desktop for Windows]: https://download.docker.com/win/stable/Docker%20Desktop%20Installer.exe
[Docker Toolbox]: https://docs.docker.com/toolbox/overview/
[Keep the Privacy]: https://github.com/sergree/matchering/wiki/Keep-the-Privacy
[hardware virtualization]: https://support.bluestacks.com/hc/en-us/articles/115003174386-How-can-I-enable-virtualization-VT-on-my-PC-for-BlueStacks-4-
[WSL 2]: https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi
