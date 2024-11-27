cd output/_dnd5e
KEYS=$(wrangler kv:key list --namespace-id $CLOUDFLARE_NAMESPACE_ID | grep -oP '"name": "\K[^"]+')
echo "Deleting Keys!"
for KEY in $KEYS; do
  wrangler kv:key delete --namespace-id $CLOUDFLARE_NAMESPACE_ID $KEY
done
echo "Uploading Keys!"
for file in $(find . -type f); do
    key=$(echo "$file" | sed -e 's|^\./||' -e 's|\.[^.]*$||')
    wrangler kv:key put "_dnd5e:$key" --path $file \
        --namespace-id $CLOUDFLARE_NAMESPACE_ID
done
