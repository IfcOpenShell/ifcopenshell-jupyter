FROM ubuntu:latest
RUN apt-get update && apt-get install -y python3 python3-pip wget
RUN pip3 install lark numpy shapely mathutils ifcopenshell
RUN wget -O model.ifc https://www.ifcwiki.org/images/e/e3/AC20-FZK-Haus.ifc
