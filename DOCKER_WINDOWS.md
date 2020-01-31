# Matchering 2.0 Docker Image

**[Docker Desktop for Windows]** requires **Microsoft Windows 10 Professional** or **Enterprise 64-bit**. 

###### For previous versions get **[Docker Toolbox]**.

1. Download and install **[Docker Desktop for Windows]**. Use the **Docker Desktop** shortcut if it doesn't start automatically after installation

2. Wait for **Docker** to load: its taskbar icon will stop moving. Close the **Login with your Docker ID** window when it appears

3. **IMPORTANT**: Increase the amount of **Memory** used by **Docker** from **2.00 GB** to **4.00 GB**:

 - Open the **Docker Desktop** menu by clicking the **Docker taskbar icon**
 
![Docker Taskbar](https://docs.docker.com/docker-for-windows/images/whale-icon-systray-hidden.png)

- Select **Settings**

![Docker Settings](https://docs.docker.com/docker-for-windows/images/docker-menu-settings.png)

 - Go to **Resouces > Advanced** tab and increase **Memory** to **4.00 GB**, click **Apply & Restart**


```
docker run -dp 8360:8360 -v mgw-data:/app/data --name mgw-app --restart always sergree/matchering-web
```


[Docker Desktop for Windows]: https://download.docker.com/win/stable/Docker%20Desktop%20Installer.exe
[Docker Toolbox]: https://docs.docker.com/toolbox/overview/
