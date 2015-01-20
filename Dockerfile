# --------------------------------------------------------------------------
# This is a Dockerfile to build an Ubuntu 14.04 Docker image with
# Kotti
#
# Use a command like:
#     docker build -t <user>/kotti .
# --------------------------------------------------------------------------

FROM  orchardup/python:2.7
MAINTAINER  Marc Abramowitz <marc@marc-abramowitz.com> (@msabramo)

RUN pip install -r https://raw.github.com/Kotti/Kotti/stable/requirements.txt
ADD app.ini .

EXPOSE 5000

CMD ["pserve", "app.ini", "host=0.0.0.0"]
