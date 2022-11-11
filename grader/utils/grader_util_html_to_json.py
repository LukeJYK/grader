# To convert html page into json, so that we can compare if two html objects are actually equal.

from html.parser import HTMLParser
import json
import re

class HtmlToJsonParser(HTMLParser):
    def __init__(self) :
        HTMLParser.__init__(self)
        self.json = []
        self.obj_stack = []

    def get_parsed_json(self):
        assert len(self.obj_stack) == 0
        return self.json

    def handle_starttag(self, tag, attrs):
        attrs = { k:v for k,v in attrs } # turn attrs into a dictionary
        self.obj_stack.append({
            "tag_name": tag,
            "attrs": attrs,
            "contents": []
        })
                 
    def handle_endtag(self, tag):
        obj = self.obj_stack.pop()
        assert tag == obj["tag_name"]
        if len(self.obj_stack) == 0: # root return
            self.json.append(obj)
        else: # child return
            self.obj_stack[-1]["contents"].append(obj)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data):
        data = re.sub("\s+", " ", data) # replace various spaces to a single space
        data = data.strip() # remove sidal spaces
        if len(data) == 0: # ignore null data
            return
        if len(self.obj_stack) == 0:
            self.json.append(data)
        else:
            self.obj_stack[-1]["contents"].append(data)

def parse(html):
    parser = HtmlToJsonParser()
    try:
        parser.feed(html)
        return parser.get_parsed_json()
    except:
        return None

if __name__ == "__main__":
    import sys
    with open(sys.argv[1], "r") as f:
        html = f.read()
    parser = HtmlToJsonParser()
    parser.feed(html)
    print(json.dumps(parser.get_parsed_json(), indent=2))