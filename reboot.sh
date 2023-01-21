#!/bin/bash
cd ~/project_dir

GIT_OUTPUT_MESSAGE=`git pull`
ALREADY_MESSAGE="Already up to date."

source app/.env

if [ "$GIT_OUTPUT_MESSAGE" != "$ALREADY_MESSAGE" ]; then
    curl \
        -H "Content-Type: application/json" \
        -X POST \
        -d "{\"content\": \"$GIT_OUTPUT_MESSAGE\"}" \
        $DISCORD_WEBHOOK_URL_REBOOT_LOG

    if [[ "$GIT_OUTPUT_MESSAGE" =~ "error" ]]; then
        exit 1
    fi

    docker-compose up -d
    curl \
        -H "Content-Type: application/json" \
        -X POST \
        -d "{\"content\": \"再起動しました。"}" \
        $DISCORD_WEBHOOK_URL_REBOOT_LOG


fi