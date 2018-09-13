FROM python:3.6

RUN apt-get -y update

# build flumine
ADD . /flumine
WORKDIR /flumine

# install py libraries
RUN pip install -r requirements.txt

CMD python main.py $STREAM_TYPE $MARKET_FILTER $MARKET_DATA_FILTER
