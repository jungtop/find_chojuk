from pathlib import Path
from fuzzysearch import find_near_matches_in_file
import time
import threading
from openpecha.core.layer import Layer, LayerEnum
from openpecha.core.pecha import OpenPechaFS
from uuid import uuid4
import yaml


def get_search_segments(search_path):
    text = Path(search_path).read_text(encoding="utf-8")
    first_seg = text[0:50]
    last_seg = text[-50:]
    len_of_text = len(text)
    mid = int(len_of_text/2)
    mid_seg = text[mid-25:mid+25]
    return (first_seg,mid_seg,last_seg)

def get_target_files(target_path):
    bases = list(Path(target_path+"/base").iterdir())
    for base in bases:
        yield base

def fuzzy_search(base_file,segments): 
    first,mid,last = segments
    first_match = check_matches(first,base_file)
    mid_match = check_matches(mid,base_file)
    last_match = check_matches(last,base_file)

    """ first_thread = threading.Thread(target=check_matches,args=(first,text))
    mid_thread = threading.Thread(target=check_matches,args=(mid,text))
    last_thread = threading.Thread(target=check_matches,args=(last,text))
    
    first_thread.start()
    mid_thread.start()
    last_thread.start()

    first_thread.join()
    mid_thread.join()
    last_thread.join() """

    if first_match and mid_match and last_match:
        return (first_match,last_match)


def check_matches(search_pattern,target_file):
    with open(target_file.as_posix(), 'r',encoding='utf8') as f:
        match = find_near_matches_in_file(search_pattern,f,max_l_dist=10)
    return match


def create_index(span,target_path,base_file):
    opf = OpenPechaFS(path=target_path)
    annotations,spans=get_annotations(span,base_file)
    index = Layer(annotation_type=LayerEnum.index,annotations=annotations)
    opf._index = index
    opf.save_index()
    instance = add_instances(spans,target_path,base_file)
    return instance

def get_annotations(span,base_file):
    page_annotations = {}
    spans = {}
    start,end = span
    spans.update({uuid4().hex:{
        "base":base_file.stem,
        "start":start,
        "end":end
    }})
    page_annotaion = {uuid4().hex:{
        "work":"chojuk",
        "work_id":"cc",
        "spans":spans
    }
    }
    page_annotations.update(page_annotaion)
    return page_annotations,spans


def get_matched_span(match):
    first_match,last_match = match
    return (first_match[0].start,last_match[0].end)

def create_work(instances):
    works = {
        "id":uuid4().hex,
        "title":"chojuk",
        "instances":instances
    }
    works_yml = toyaml(works)
    Path("./find_chojuk/works.yml").write_text(works_yml)

def toyaml(dict):
    return yaml.safe_dump(dict, sort_keys=False, allow_unicode=True)

def add_instances(spans,target_path,base_file):
    instance = {
        uuid4().hex:{
            "pecha_id":Path(target_path).stem,
            "spans":spans
        }

    }
    return instance

if __name__ == "__main__":
    search_path = "./find_chojuk/O96FB467A/O96FB467A/O96FB467A.opf/base/03EC.txt"
    target_path = "./find_chojuk/P000800/P000800.opf"
    segments = get_search_segments(search_path)
    time_past = time.time()
    instances = []
    for base_file in get_target_files(target_path):
        match = fuzzy_search(base_file,segments)
        if match:
            span = get_matched_span(match)
            instance = create_index(span,target_path,base_file)
            instances.append(instance)
    create_work(instance)

    print(time.time()-time_past)


#module to handle if there is more than one match in first,mid,last   