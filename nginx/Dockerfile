# Use the official nginx Alpine image
FROM nginx:alpine

# Remove the default nginx.conf
RUN rm /etc/nginx/conf.d/default.conf

# Copy SSL certificates
COPY certs /etc/nginx/certs

# Copy a custom nginx config file into the container
COPY nginx.conf /etc/nginx/conf.d/

# Expose port 80 for Nginx
EXPOSE 80 443

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]