#!/bin/bash
# Script to set up an rtsp processor that handles incoming RTSP streams and format them for Perch
set -e

# Find current user in case it is not pi
echo "Detecting current user..."
CURRENT_USER=$(logname)
# print the current user
echo "Working as: $CURRENT_USER"
# Run an update on the system before making other changes
echo "Updating system..."
sudo apt update 

# Install make sure ffmpeg is installed
echo "Checking for and installing ffmpeg..."
sudo apt install -y ffmpeg

# Configure first stream
# Ask user for the short name of the first stream to configure
read -p "Enter the short name of the first stream to configure: " STREAM_NAME
# ask user for the rtsp url for the first stream
read -p "Enter the RTSP URL for the first stream, include rtsp://: " RTSP_URL
# ask the user for the desired output directory for processed clips
read -p "Enter the desired output directory for processed clips (full path): " OUT_DIR

# Copy the Template files to the correct locations
# Check that /etc/rtsp-streamer exists
if [ ! -d /etc/rtsp-streamer ]; then
  echo "Creating /etc/rtsp-streamer directory..."
  sudo mkdir -p /etc/rtsp-streamer
fi

# Create the environment file directly
echo "Creating environment file for $STREAM_NAME..."
sudo bash -c "cat > /etc/rtsp-streamer/$STREAM_NAME.env" <<EOL
RTSP_URL=$RTSP_URL
OUT_DIR=$OUT_DIR
EOL

# ask user if they want to configure any other streams
read -p "Do you want to configure another stream? (y/n): " CONFIGURE_ANOTHER

while [[ "$CONFIGURE_ANOTHER" == "y" ]]; do
    read -p "Enter the short name of the stream to configure: " STREAM_NAME
    read -p "Enter the RTSP URL for the stream, include \"rtsp://\": " RTSP_URL
    read -p "Enter the desired output directory for processed clips (full path): " OUT_DIR

    # Create the environment file directly
    echo "Creating environment file for $STREAM_NAME..."
    sudo bash -c "cat > /etc/rtsp-streamer/$STREAM_NAME.env" <<EOL
RTSP_URL=$RTSP_URL
OUT_DIR=$OUT_DIR
EOL

  read -p "Do you want to configure another stream? (y/n): " CONFIGURE_ANOTHER
done

# copy the service file and replace the username and group with the user's info
echo "Copying service file..."
sudo cp ./rtsp-processing/perch-rtsp@.service /etc/systemd/system/
sudo sed -i "s/{{USER}}/$CURRENT_USER/g" /etc/systemd/system/perch-rtsp@.service
sudo sed -i "s|{{GROUP}}|$CURRENT_USER|g" /etc/systemd/system/perch-rtsp@.service

# enable and start the processor for each created stream
for STREAM in /etc/rtsp-streamer/*.env; do
  STREAM_NAME=$(basename "$STREAM" .env)
  echo "Enabling and starting service for $STREAM_NAME..."
  sudo systemctl enable "perch-rtsp@$STREAM_NAME.service"
  sudo systemctl start "perch-rtsp@$STREAM_NAME.service"
  # wait for a few seconds to allow the service to start
  sleep 5
  # check status of service
  sudo systemctl status "perch-rtsp@$STREAM_NAME.service" --no-pager
done

echo "All services have been enabled and started. Check outputs for errors with the services"

# setup the pruning service
echo "Setting up pruning service..."
sudo cp ./rtsp-processing/perch-prune@.service /etc/systemd/system/
#replace the user and group with the user's info
sudo sed -i "s/{{USER}}/$CURRENT_USER/g" /etc/systemd/system/perch-prune@.service
sudo sed -i "s|{{GROUP}}|$CURRENT_USER|g" /etc/systemd/system/perch-prune@.service

# setup the service for each configured rtsp stream
for STREAM in /etc/rtsp-streamer/*.env; do
  STREAM_NAME=$(basename "$STREAM" .env)
  echo "Enabling and starting service for $STREAM_NAME..."
  sudo systemctl daemon-reload
  sudo systemctl enable "perch-prune@$STREAM_NAME.service"
  #sudo systemctl start "perch-prune@$STREAM_NAME.service"

  # wait for a few seconds to allow the service to start
  #sleep 5
  # check status of service
  #sudo systemctl status "perch-prune@$STREAM_NAME.service" --no-pager
done

echo "All pruning services have been enabled, check for errors in the outputs"

# enable timers
echo "Enabling timers..."
sudo cp ./rtsp-processing/perch-prune@.timer /etc/systemd/system/
# enable all timers
for STREAM in /etc/rtsp-streamer/*.env; do
  STREAM_NAME=$(basename "$STREAM" .env)
  echo "Enabling and starting timer for $STREAM_NAME..."
  sudo systemctl daemon-reload
  sudo systemctl enable "perch-prune@$STREAM_NAME.timer"
  sudo systemctl start "perch-prune@$STREAM_NAME.timer"
  # wait for a few seconds to allow the timer to start
  sleep 5
  # check status of timer
  sudo systemctl status "perch-prune@$STREAM_NAME.timer" --no-pager
done


echo "All pruning timers have been enabled, check for errors in the outputs"
echo "all setup complete, audio clips should be populating into the specified folders"