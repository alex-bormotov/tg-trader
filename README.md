## Features

> This bot it like a Telegram interface for Binance exchange

> Multiple exchange accounts, switch between them

> Show wallet balances, per coin and all positive

> Placing limit orders, and canceling them

> Changing orders status notification

> Showing open orders

> Show coin prices

---

> [Install](#install)

> [Update](#Update)

> [Say Me Thanks :)](#Donate)

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

##### Donate

> If my code was useful for you may buy me coffee:

> [My Binance Referal Link](https://www.binance.com/en/register?ref=35560900)

> ETH 0x4a92Eb0b09Dc2DC27D2C2a35f5A28eF7969dE528
