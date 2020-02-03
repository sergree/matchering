# Linux - Matchering 2.0 Docker Image

1. Install **Docker Engine - Community** for:
- [CentOS](https://docs.docker.com/install/linux/docker-ce/centos/)
- [Debian](https://docs.docker.com/install/linux/docker-ce/debian/)
- [Fedora](https://docs.docker.com/install/linux/docker-ce/fedora/)
- [Ubuntu](https://docs.docker.com/install/linux/docker-ce/ubuntu/)
- [Binaries](https://docs.docker.com/install/linux/docker-ce/binaries/)
2. *(Optional) Follow **[Post-installation steps for Linux](https://docs.docker.com/install/linux/linux-postinstall/)***
3. Run this command in the terminal:
```
docker run -dp 8360:8360 -v mgw-data:/app/data --name mgw-app --restart always sergree/matchering-web
```
4. Enjoy your **Matchering 2.0** at 🎉 **http://127.0.0.1:8360** 🎉 It will also run automatically at startup

### IMPORTANT: Read the [Keep the Privacy] page if you would like to host our web application publicly!

## Updating

1. Open the terminal
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

[Keep the Privacy]: https://github.com/sergree/matchering/wiki/Keep-the-Privacy
