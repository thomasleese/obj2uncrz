import argparse
import collections
import math
import os
import sys
import time


from decimal import Decimal as Number # change to float if you don't need arbitary precision


class Material:
    def __init__(self, name):
        self.name = name


class ModelGroup:
    def __init__(self, obj, name):
        self.obj = obj
        self.name = name
        self.faces = []
        self.material = None

    def convert_face_inst(self, face):
        new_position = None
        new_normal = None
        new_colour = None
        new_texcoord = None

        if face[0]: new_position = self.obj.model.positions[face[0] - 1]
        if face[1]: new_texcoord = self.obj.model.texcoords[face[1] - 1]
        if face[2]: new_normal = self.obj.model.normals[face[2] - 1]

        return (new_position, new_normal, new_colour, new_texcoord)

    def convert_face(self, face):
        return [self.convert_face_inst(x) for x in face]


class ModelObject:
    def __init__(self, model, name):
        self.model = model
        self.name = name
        self.groups = []

    def create_group(self, name):
        grp = ModelGroup(self, name)
        self.groups.append(grp)
        return grp


class Model:
    def __init__(self, name):
        self.name = name
        self.materals = []
        self.objects = []

        self.positions = []
        self.normals = []
        self.texcoords = []

    def create_object(self, name):
        obj = ModelObject(self, name)
        self.objects.append(obj)
        return obj

    def find_object(self, name):
        for o in self.objects:
            if o.name == name:
                return o
        else:
            print("Warning, no object found for", name)
            return None


class DescriptionVertex:
    def __init__(self, position, normal, colour, texCoords, segment):
        self.position = position
        self.normal = normal
        self.colour = colour
        self.texCoords = texCoords
        self.segment = segment
        self.matched = False

    def __eq__(self, other):
        return self.position == other.position and self.normal == other.normal and self.colour == other.colour and self.texCoords == other.texCoords and self.segment == other.segment


class DescriptionSegment:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.type = "seg"
        self.segments = []
        self.obj = None
        self.origin = (Number(0), Number(0), Number(0))
        self.match = []
        self.prop = None


class DescriptionSection:
    def __init__(self, name):
        self.name = name
        self.material = None
        self.faces = []
        self.attributes = []


class DescriptionModel:
    def __init__(self, name):
        self.name = name
        self.model = None
        self.flip_z = False
        self.match_mode = "changetti"
        self.match_normals = False
        self.manual_normals = False

        self.segments = []
        self.vertices = []
        self.sections = []


class Description:
    def __init__(self, name):
        self.name = name
        self.models = []


class TokenFile:
    def __init__(self, filename):
        self.filename = filename
        self.fp = None

    def open(self, mode):
        if not self.fp:
            if mode == "r":
                print(" > Reading", self.filename)
            else:
                print(" > Writing", self.filename)

            self.fp = open(self.filename, mode)

    def read(self):
        self.open("r")

        lines = []

        for line in self.fp:
            line = line.strip()
            if len(line) != 0 and not line.startswith("//") and not line.startswith("#"):
                tokens = line.split(" ")
                lines.append(tokens)

        return lines

    def write(self, *tokens):
        self.open("w")

        self.fp.write(" ".join([str(x) for x in tokens]) + "\n")

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.fp.close()
        return False


class Converter:
    def read_mtl(self, filename):
        materials = []
        material = None

        with TokenFile(filename) as fp:
            for tokens in fp.read():
                if tokens[0] == "newmtl":
                    material = Material(tokens[1])
                elif tokens[0] == "Ns":
                    pass
                elif tokens[0] == "d":
                    pass
                elif tokens[0] == "illum":
                    pass
                elif tokens[0] == "map_Kd":
                    pass
                elif tokens[0] == "Kd":
                    pass
                elif tokens[0] == "Ka":
                    pass
                elif tokens[0] == "Ks":
                    pass
                elif tokens[0] == "Ke":
                    pass
                else:
                    print(tokens)

        return materials

    def read_obj(self, filename):
        def parse_obj_index(index):
            tokens = index.split("/")
            if len(tokens) == 1:
                return ( int(tokens[0]), None, None )
            elif len(tokens) == 2:
                return ( int(tokens[0]), int(tokens[1]), None )
            elif len(tokens) == 3 and tokens[1] == "":
                return ( int(tokens[0]), None, int(tokens[2]) )
            elif len(tokens) == 3:
                return ( int(tokens[0]), int(tokens[1]), int(tokens[2]) )

            return None

        with TokenFile(filename) as fp:
            name = os.path.splitext(os.path.basename(filename))[0]

            mdl = Model(name)
            obj = None
            grp = None

            for tokens in fp.read():
                if tokens[0] == "mtllib":
                    mtl_filename = os.path.join(os.path.dirname(filename), tokens[1])
                    mdl.materals += self.read_mtl(mtl_filename)
                elif tokens[0]== "o":
                    obj = mdl.create_object(tokens[1])
                elif tokens[0] == "v":
                    vertex = [ Number(1), Number(1), Number(1), Number(1) ]

                    try:
                        vertex = [ Number(tokens[1]), Number(tokens[2]), Number(tokens[3]), Number(tokens[4]) ]
                    except IndexError:
                        vertex = [ Number(tokens[1]), Number(tokens[2]), Number(tokens[3]), 1.0 ]

                    mdl.positions.append(vertex)
                elif tokens[0] == "vn":
                    normal = [ Number(tokens[1]), Number(tokens[2]), Number(tokens[3]) ]
                    mdl.normals.append(normal)
                elif tokens[0] == "vt":
                    texcoords = [ 1.0, 1.0, 1.0 ]

                    try:
                        texcoords = [ Number(tokens[1]), Number(tokens[2]), Number(tokens[3]) ]
                    except:
                        texcoords = [ Number(tokens[1]), Number(tokens[2]), 1.0 ]

                    mdl.texcoords.append(texcoords)
                elif tokens[0] == "g":
                    grp = obj.create_group(tokens[1])
                elif tokens[0] == "usemtl":
                    grp.material = tokens[1]
                elif tokens[0] == "f":
                    if not grp: grp = obj.create_group("group")

                    face = tuple([ parse_obj_index(x) for x in tokens[1:] ])
                    grp.faces.append(grp.convert_face(face))
                elif tokens[0] == "s":
                    pass # explicitly ignore
                else:
                    print(tokens)

            return mdl

    def read_undsc(self, filename):
        desc = Description(filename)
        model = None
        segment = None
        section = None

        with TokenFile(filename) as fp:
            for tokens in fp.read():
                if tokens[0] == "mdl":
                    model = DescriptionModel(tokens[1])
                    segment = model
                    desc.models.append(model)
                elif tokens[0] == "flipz":
                    model.flip_z = True
                elif tokens[0] == "matchmode":
                    model.match_mode = tokens[1]
                elif tokens[0] == "matchnormals":
                    model.match_normals = True
                    model.manual_normals = True
                elif tokens[0] == "manualnormals":
                    model.manual_normals = True
                elif tokens[0] == "objfile":
                    obj_filename = os.path.join(os.path.dirname(filename), tokens[1])
                    desc.model = self.read_obj(obj_filename)
                elif tokens[0] == "seg" or tokens[0] == "blend":
                    new_segment = DescriptionSegment(tokens[1], segment)
                    if tokens[0] == "blend":
                        new_segment.type = "blend"
                        new_segment.prop = Number(tokens[2])
                    segment.segments.append(new_segment)
                    segment = new_segment
                elif tokens[0] == "sec":
                    section = DescriptionSection(tokens[1])
                    model.sections.append(section)
                elif tokens[0] == "mtl":
                    section.material = tokens[1]
                elif tokens[0] == "obj":
                    segment.obj = desc.model.find_object(tokens[1])
                elif tokens[0] == "origin":
                    segment.origin = ( Number(tokens[1]), Number(tokens[2]), Number(tokens[3]) )
                elif tokens[0] == "match":
                    segment.match.append(tokens[1])
                elif tokens[0] == "end" and (tokens[1] == "seg" or tokens[1] == "blend"):
                    segment = segment.parent
                elif tokens[0] == "end" and tokens[1] == "sec":
                    section = None
                elif tokens[0] == "end" and tokens[1] == "mdl":
                    model = None
                    segment = None
                elif tokens[0] in [ "shader_dx9", "colmod", "technique", "technique_light", "technique_decal", "technique_over", "texture", "lighting", "alpha" ]:
                    if section:
                        section.attributes.append(tokens)
                else:
                    print(tokens)

        def process_segment(segment, model, indent = 0):
            print("  " + (" " * indent) + " > Processing", segment.name, end = " ")

            start_time = time.time()
            if segment.obj:
                for group in segment.obj.groups:
                    for faces in group.faces:
                        new_face = [ ]

                        for face in faces:
                            position = list(face[0] or [ Number(0), Number(0), Number(0) ])
                            normal = list(face[1] or [ Number(0), Number(0), Number(0) ])
                            colour = list(face[2] or [ Number(1), Number(1), Number(1), Number(1) ])
                            texCoords = list(face[3] or [ Number(0), Number(0) ])
                            vertex = DescriptionVertex(position, normal, colour, texCoords, segment)

                            if vertex in model.vertices:
                                for i, v in enumerate(model.vertices):
                                    if v == vertex:
                                        new_face.append(i)
                                        break
                            else:
                                new_face.append(len(model.vertices))
                                model.vertices.append(vertex)

                        for section in model.sections:
                            if section.material == group.material:
                                section.faces.append(new_face)

            duration = time.time() - start_time
            print("took", str(int(duration * 1000)) + "ms")

            for segment2 in segment.segments:
                process_segment(segment2, model, indent + 2)

        print(" > Processing model segments")

        for model in desc.models:
            for segment in model.segments:
                process_segment(segment, model)

            # vertex z-flip
            if model.flip_z:
                for v in model.vertices:
                    v.position[2] = -v.position[2]
                    v.normal[2] = -v.normal[2]
                    v.texCoords[1] = 1 - v.texCoords[1]

            # matching
            for v1 in model.vertices:
                if v1.matched:
                    continue

                same_vertices = []
                do_match = False
                for v2 in model.vertices:
                    if v1.position == v2.position:
                        if v2.segment == v1.segment:
                            same_vertices.append(v2)
                        else:
                            for m in v2.segment.match:
                                if v1.segment.name == m:
                                    same_vertices.append(v2)
                                    do_match = True
                                    break

                if do_match:
                    if model.match_normals:
                        x = Number(str(sum([ v.normal[0] for v in same_vertices ]) / len(same_vertices)))
                        y = Number(str(sum([ v.normal[1] for v in same_vertices ]) / len(same_vertices)))
                        z = Number(str(sum([ v.normal[2] for v in same_vertices ]) / len(same_vertices)))

                        l = Number(str(math.sqrt(x * x + y * y + z * z)))
                        x /= l
                        y /= l
                        z /= l

                        for v in same_vertices:
                            v.normal = [ x, y, z ]

                    for v2 in same_vertices:
                        v2.matched = True
                        if model.match_mode == "changetti":
                            v2.segment = v1.segment

            # subtract origins
            for v in model.vertices:
                if v.segment.type == "blend":
                    v.position[0] -= v.segment.parent.origin[0]
                    v.position[1] -= v.segment.parent.origin[1]
                    v.position[2] -= v.segment.parent.origin[2]
                else:
                    v.position[0] -= v.segment.origin[0]
                    v.position[1] -= v.segment.origin[1]
                    v.position[2] -= v.segment.origin[2]

            # face z-flip
            if model.flip_z:
                for section in model.sections:
                    for face in section.faces:
                        tmp = face[1]
                        face[1] = face[2]
                        face[2] = tmp

            # replace vertex indexes (only need this in the other matchmode hting)

        return desc

    def write_uncrz(self, description, filename):
        def write_uncrz_segment(segment, model, fp):
            fp.write()

            if segment.type == "seg":
                fp.write("seg", segment.name)

                fp.write()

                if hasattr(segment.parent, "origin"):
                    offset_x = segment.origin[0] - segment.parent.origin[0]
                    offset_y = segment.origin[1] - segment.parent.origin[1]
                    offset_z = segment.origin[2] - segment.parent.origin[2]
                    fp.write("offset", offset_x, offset_y, offset_z)
                else:
                    fp.write("offset", 0, 0, 0)

                fp.write("rotation", 0, 0, 0)
            elif segment.type == "blend":
                fp.write("blend", segment.name, segment.prop)

            fp.write()

            for segment2 in segment.segments:
                write_uncrz_segment(segment2, model, fp)

            fp.write()

            fp.write("end", segment.type, "// " + segment.name)

            fp.write()

        with TokenFile(filename) as fp:
            for model in description.models:
                fp.write()

                fp.write("mdl", model.name)

                fp.write()

                fp.write("vertex", "PCT")
                if model.manual_normals:
                    fp.write("manualnormals")

                fp.write()

                for segment in model.segments:
                    write_uncrz_segment(segment, model, fp)

                fp.write()

                for vertex in model.vertices:
                    tokens = [ ]
                    tokens[0:3] = vertex.position[0:3]
                    tokens[3:6] = vertex.normal[0:3]
                    tokens[6:9] = vertex.colour[0:3]
                    tokens[9:11] = vertex.texCoords[0:2]

                    if not model.manual_normals:
                        del tokens[3:6]

                    fp.write("v", *tokens)
                    fp.write("lpt", vertex.segment.name)

                fp.write()

                for section in model.sections:
                    fp.write("sec", section.name)

                    fp.write()

                    for attr in section.attributes:
                        fp.write(*attr)

                    fp.write()

                    for face in section.faces:
                        fp.write("f", *face)

                    fp.write()

                    fp.write("end", "sec", "// " + section.name)

                    fp.write()

                fp.write("end", "mdl", "// " + model.name)

                fp.write()

    def convert(self, in_filename):
        start_time = time.time()

        out_filename = os.path.splitext(in_filename)[0] + ".uncrz"
        print("Converting", in_filename, "->", out_filename)

        description = self.read_undsc(in_filename)
        self.write_uncrz(description, out_filename)

        for model in description.models:
            print(" > Model", model.name, "has", len(model.vertices), "vertices")

            for section in model.sections:
                print("   > Section", section.name, "has", len(section.faces), "faces")

        duration = time.time() - start_time
        print(" > Conversion took", str(int(duration * 1000)) + "ms")


def main():
    parser = argparse.ArgumentParser(description="Convert from Wavefront OBJ to UNCRZ.")
    parser.add_argument("files", nargs="+", help="UNCRZ description files for use as input")
    args = parser.parse_args()

    for filename in args.files:
        Converter().convert(filename)


if __name__ == "__main__":
    main()
