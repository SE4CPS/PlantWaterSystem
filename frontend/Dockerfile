# Step 1: Build the React app
FROM node:16 AS build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY web-app/package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend code
COPY web-app/ .

# RUN npm install react-router-dom

# Build the React app (for production build)
RUN npm run build

# Expose port 3000
EXPOSE 3000

# Step 2: Serve the React app using npm start (for development)
CMD ["npm", "start"]
