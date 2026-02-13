# frontend/Dockerfile
#
# Nginx static server:
# - serves AngularJS files from /usr/share/nginx/html
# - reverse proxies /api/ to backend:8000 to avoid CORS issues

FROM nginx:alpine


COPY . /usr/share/nginx/html

# Sobrescreve config default do nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Run Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
