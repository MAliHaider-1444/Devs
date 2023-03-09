If all works, this is all that is needed to start:

`docker compose -f "docker-compose.yml" up -d --build`

Sometimes (network issues I think), you might have to run these steps:

`docker compose  -f "docker-compose.yml" up -d --build postgres-setup-1 postgres-setup-2`

Grafana needs the postgres datasource added (and dashboards). Here is a blog explaining how that might be accomplished during build time: https://community.grafana.com/t/data-source-on-startup/8618/2