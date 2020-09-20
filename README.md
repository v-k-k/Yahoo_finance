# Yahoo_finance test

## To build the project use docker with command *"docker build -t yahoo ."*

## Then launch the project with command *"docker run --name yahoo -p 5000:5000 yahoo"*

## Open url *"http://localhost:5000/"* with your browser 

## All the logs would be displayed in your termiinal, and after successful exucution you would see result JSON in your browser

## To copy collected CSV files use command *"docker cp yahoo:/usr/src/app/csv_volume <- desired local folder ->"*
