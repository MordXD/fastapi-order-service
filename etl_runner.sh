
export PGPASSWORD=$POSTGRES_PASSWORD

while true; do
  echo "$(date): Running daily ETL job..."
  psql -h db -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT refresh_daily_sales((CURRENT_DATE - INTERVAL '1 day')::DATE);"
  echo "$(date): ETL job finished. Sleeping for 24 hours."
  sleep 86400
done