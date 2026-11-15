#!/usr/bin/env bash
# Build the site here and publish it on musicroombot.
#   deploy/deploy.sh            build, sync dist/ and deploy/, (re)start the container
# The server keeps only deploy/ and dist/ in ~/ism-website; no Node needed there.
set -euo pipefail
cd "$(dirname "$0")/.."
HOST=${HOST:-musicroombot}
DIR=${DIR:-ism-website}

npm run check
npm test
npm run build

ssh "$HOST" "mkdir -p ~/$DIR/dist ~/$DIR/deploy"
rsync -az --delete deploy/ "$HOST:$DIR/deploy/"
# --delay-updates moves all new files into place at the end, so a page never
# references a bundle that has not arrived yet.
rsync -az --delete --delay-updates dist/ "$HOST:$DIR/dist/"
ssh "$HOST" "cd ~/$DIR/deploy && docker compose -p ism up -d && docker compose -p ism ps"
ssh "$HOST" "curl -fsS -o /dev/null -w '%{http_code} / \n' http://127.0.0.1:8796/ && curl -s -o /dev/null -w '%{http_code} /missing\n' http://127.0.0.1:8796/missing"
