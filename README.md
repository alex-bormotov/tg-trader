# tg-trader



## Features

> Multiple exchange accounts, switch between them.

> Show wallet balances

> Manual trading on Binance Exchange

> Place limit orders, show and cancel them

> Show coin prices


---

### Install

```bash
sudo apt-get update
```

```bash
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
```

```bash
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
```

```bash
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
```

```bash
sudo apt-get update
```

```bash
sudo apt-get install docker.io git
```

```bash
git clone https://github.com/alex-bormotov/tg-trader
```

```bash
cd tg-trader
```

```bash
cp config.json.sample config.json
```

> edit config.json

```bash
sudo docker build -t tg-trader .
```

```bash
sudo docker run tg-trader &
```
---

### Update

```bash
cd tg-trader
```

```bash
sudo docker ps
```

```bash
sudo docker stop CONTAINER ID
```

```bash
sudo docker rm CONTAINER ID
```

```bash
sudo docker rmi tg-trader
```

```bash
git pull origin master
```

```bash
sudo docker build -t tg-trader .
```

```bash
sudo docker run tg-trader &
```
---

### Donate

> If you would like to buy me a coffee  3K9ocinkiUUqkBj9BqvFVsUgW2uMLqZFcP (BTC)
