<div align="center">
  <h1>🎨 PicAIsso</h1>
  <img src="img/logo.png" width="200" height="200" />
  <p><em>PicAIsso: Bring AI art to your life.</em></p>
</div>

**PicAIsso** is an open-source StableDiffusion implementation for generating AI art using an API and a Discord Bot.

👉 _Imagine self-hosting your own MidJourney Discord bot, but with a different name and a different art style._

---

## Requirements

- [Docker](https://docs.docker.com/get-docker/) installed
- NVIDIA GPU with at least 16GB of VRAM
- NVIDIA drivers installed + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker) installed
- Linux based OS
> Please Windows users, go dual-boot, unfortunatly I don't have any experience with Windows and Docker.

## Installation

1. Clone the repository
```bash
git clone https://github.com/chainyo/picaisso.git
```

2. Create your own `.env` file for the API and update the values with your own. 
> Follow the `.env.template` comments.

3. Create your own `.env` file for the Discord Bot and update the values with your own. 
> Follow the `.env.template` comments. The Discord bot application is explained if you follow the link in the `.env.template` file.

4. (Optional) If you want to store the generated images, there is a S3 bucket configuration in the `.env` file. 
You can create your own S3 bucket and update the values with your own. Leave the values empty if you don't want to use S3.

## Deployment

There are two steps:
- Deploy the API
- Deploy the Discord Bot

**Warning:** Be sure to be in the root folder of the project before running the Docker commands.

### Create the Docker network

```bash
docker network create picaisso
```

### Deploy the API

1. Build the Docker image
```bash
docker build -t picaisso-api:latest -f docker/api/Dockerfile .
```

You should see the built image in your Docker images list, you can check it with the following command:
```bash
docker images
```
![picaisso-api](img/docker-images-api.png)

2. Run the Docker container
```bash
docker run -d \
  --gpus all \
  --network picaisso \
  -p 7680:7680 \
  -v ${HOME}/.cache:/root/.cache \
  --restart unless-stopped \
  --name picaisso-api \
  picaisso-api:latest
```

3. Test the API

The API should be running on port `7680` of your machine. It can take a few minutes to start, because the model has
to be downloaded and loaded on the first run. Because we are using the `${HOME}/.cache`folder as a mounted volume, the model will be downloaded only once and will be reused on the next runs.

Once the API is running, you can test it by going to `http://localhost:7680/` in your web browser.

You should see the landing page of the API.

![landing-page-picaisso-api](img/api-landing-page.png)

Click on the `Docs` button to see the API documentation and test the `/generate` endpoint. Check the [Usage](##usage) section for more details.

_Trouble shooting: use the `docker logs picaisso-api` command to see the logs of the container._

### Deploy the Discord Bot

1. Build the Docker image

```bash
docker build -t picaisso-bot:latest -f docker/bot/Dockerfile .
```

2. Run the Docker container

```bash
docker run -d \
  --restart unless-stopped \
  --network picaisso \
  --name picaisso-bot \
  picaisso-bot:latest
```

If you successfully created the Discord bot application, you just need to invite it to your server. You can find the invite link in the `OAuth2` section of your Discord bot application.
(See the tutorial link in the `.env.template` file.)

Mine is live! 🎉

![picaisso-bot](img/bot-online.png)

## Usage

WIP...