import bpy
import hashlib

from . import common

bl_info = {
    "name": "Bendy Bone Setup Auto",
    "author": "Uiler",
    "version": (0, 3),
    "blender": (3, 0, 0),
    "location": "Rigging",
    "description": "Setup automatically bendy bone.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Rigging"
}

#########################################################
# Constants
#########################################################
_PARENTS_BONE_TYPE_USE_ORIGINAL = "Use original"
_PARENTS_BONE_TYPE_SPECIFIC = "Specific Bone"
_ADD_DRIVER_TYPE_SELF = "Self"
_ADD_DRIVER_TYPE_NEW_ARMATRUE = "New"
_ADD_DRIVER_TYPE_SPECIFIC = "Specific"
_CONSTRAINTS_NAME_STRETCH_TO = "Stretch to bendy bone(Auto)"
_DRIVER_HANDLE_LOC_OFFSET = 0.25
_TRANSMITTER_CONSTRAINTS_NAME = "Copy Transforms(Transmitter for driver bone)"
_RENAME_BONES_INCREMENTAL_TYPE_NONE = "None"
_RENAME_BONES_INCREMENTAL_TYPE_ALPHA = "Alphabet"
_RENAME_BONES_INCREMENTAL_TYPE_NUMBER = "Number"
_RENAME_BONES_ALPHABET_CASE_UPPER = common.LETTERS_CASE_TYPE_UPPER
_RENAME_BONES_ALPHABET_CASE_LOWER = common.LETTERS_CASE_TYPE_LOWER
#########################################################
# Global Variables
#########################################################
#########################################################
# Class
#########################################################


class DriverHandleBoneInfo:

    INOUT_TYPE_IN = "in"
    INOUT_TYPE_OUT = "out"

    name = ""
    align_roll_vec = None
    head_vec = None
    tail_vec = None
    length = 0.0
    parentNm = ""
    parentVec_h = None
    parentVec_t = None
    parentRoll = None
    parentElm = None
    bone_thin = 0.0
    driver_target_nm = ""
    inout_type = ""

#########################################################
# Properties
#########################################################


def _updateRenameXAxisMirror(self, context):

    propgrp = self

    if not propgrp.rename_bones_is_mirror:
        return

    bones = context.active_object.pose.bones
    expNameList = []
    for item in propgrp.rename_bones_grp:
        if item.name not in bones.keys():
            continue

        if item.name in expNameList:
            continue

        bone = bones[item.name]
        elm = common.getNameElements(bone)
        if elm.mirror_bonename in bones.keys():
            propgrp.rename_bones_grp.remove(item.idx)
            expNameList.append(elm.mirror_bonename)

            _reNumberPropIdx(context)


class RenameBoneNamePropGrp(bpy.types.PropertyGroup):
    '''name: bpy.props.StringProperty() '''
    id: bpy.props.IntProperty()


class RenameBoneItemsPropGrp(bpy.types.PropertyGroup):
    '''name: bpy.props.StringProperty() '''
    id: bpy.props.IntProperty()
    idx: bpy.props.IntProperty()
    bone_names: bpy.props.CollectionProperty(type=RenameBoneNamePropGrp)


class SetupBendyBoneProperties(bpy.types.PropertyGroup):

    # System setting properties
    handle_size_ratio: bpy.props.FloatProperty(name="handle_size_ratio", description="Ratio of handle bones size.Default is base bones * 0.3.", default=0.3, step=0.1, subtype='NONE')
    handle_size: bpy.props.FloatProperty(name="handle_size", description="Size of handle bones.", default=0.8, step=0.1, subtype='NONE')
    driver_handle_size_ratio: bpy.props.FloatProperty(name="driver_handle_size_ratio", description="Ratio of driver handle bones.(ex handle bones length * 0.8)", default=0.8, step=0.1, subtype='NONE')
    bbone_scale_ratio: bpy.props.FloatProperty(name="bbone_scale_ratio", description="Ratio of bendy bones scale.", min=0.000001, default=0.17, step=0.1, subtype="NONE")
    bbone_scale: bpy.props.FloatProperty(name="bbone_scale", description="Scale of bendy bones.", min=0.000001, default=0.03, step=0.1, subtype="NONE")
    handle_identifier: bpy.props.StringProperty(name="handle_identifier", description="identifier of handle bone.(ex:bone_L -> hdl_head_bone_L/hdl_tail_bone_L)", default="hdl", subtype='NONE')
    head_identifier: bpy.props.StringProperty(name="head_identifier", description="head identifier of handle bone.(ex:bone_L -> hdl_head_bone_L/hdl_tail_bone_L)", default="head", subtype='NONE')
    tail_identifier: bpy.props.StringProperty(name="tail_identifier", description="tail identifier of handle bone.(ex:bone_L -> hdl_head_bone_L/hdl_tail_bone_L)", default="tail", subtype='NONE')
    is_mirror: bpy.props.BoolProperty(name="is_mirror", description="Setup X-Axis Mirror Bone.", default=True, subtype='NONE')
    is_add_driver_handle: bpy.props.BoolProperty(name="is_add_driver_handle", description="Add driver bones that transforms handle offset values.(in_x,out_x,...,scale_x,...,roll_x etc)", default=False, subtype="NONE")
    is_use_active_value: bpy.props.BoolProperty(name="is_use_active_value", description="Use values of active edit bone to default.", default=True, subtype="NONE")
    is_create_parent_of_handles: bpy.props.BoolProperty(name="is_create_parent_of_handles", description="Create parents of each handle bones of head and tail.", default=True, subtype="NONE")
    is_edit_curveonly: bpy.props.BoolProperty(name="is_edit_curveonly", description="Edit only curve variables.", default=False, subtype="NONE")
    is_edit_curve: bpy.props.BoolProperty(name="is_edit_curve", description="Edit curve variables.", default=True, subtype="NONE")
    is_add_handles: bpy.props.BoolProperty(name="is_add_handles", description="Add handles of bendy bones.", default=True, subtype="NONE")
    parents_bone_type_it = []
    parents_bone_type_it.append((_PARENTS_BONE_TYPE_USE_ORIGINAL, _PARENTS_BONE_TYPE_USE_ORIGINAL, "Set parent of handle bones to original one of selected bones.", "", 0))
    parents_bone_type_it.append((_PARENTS_BONE_TYPE_SPECIFIC, _PARENTS_BONE_TYPE_SPECIFIC, "Set parent of handle bones to a specific bone.", "", 1))
    parents_bone_type: bpy.props.EnumProperty(items=parents_bone_type_it, default=_PARENTS_BONE_TYPE_USE_ORIGINAL)
    specific_parents_bone_target: bpy.props.StringProperty(name="specific_parents_bone_target", description="Set parent to specific bone.", default="", subtype='NONE')
    driver_handle_in_identifier: bpy.props.StringProperty(name="driver_handle_in_identifier", description="identifier of handle bone of curve-in driver.(ex:bone_L -> hdl_coi_bone_L)", default="coi", subtype="NONE")
    driver_handle_out_identifier: bpy.props.StringProperty(name="driver_handle_out_identifier", description="identifier of handle bone of curve-out driver.(ex:bone_L -> hdl_coo_bone_L)", default="coo", subtype="NONE")
    add_driver_type_it = []
    add_driver_type_it.append((_ADD_DRIVER_TYPE_SELF, _ADD_DRIVER_TYPE_SELF, "Add driver bones to self.", "", 0))
    add_driver_type_it.append((_ADD_DRIVER_TYPE_NEW_ARMATRUE, _ADD_DRIVER_TYPE_NEW_ARMATRUE, "Add new armature, and add driver bones to it.", "", 1))
    add_driver_type_it.append((_ADD_DRIVER_TYPE_SPECIFIC, _ADD_DRIVER_TYPE_SPECIFIC, "Add driver bones to specific armature.", "", 2))
    add_driver_type: bpy.props.EnumProperty(items=add_driver_type_it, default=_ADD_DRIVER_TYPE_SELF)
    specific_add_driver_target: bpy.props.StringProperty(name="specific_add_driver_target", description="Target of adding driver bones of handle offset values.(in_x,out_x,...,scale_x,...,roll_x etc).", default="", subtype='NONE')
    new_name_for_driver_target: bpy.props.StringProperty(name="specific_add_driver_target", description="Create new Armature and it is the target of adding driver bones of handle offset values.(in_x,out_x,...,scale_x,...,roll_x etc).", default="New Armature", subtype='NONE')
    is_create_driver_parent_transmitter: bpy.props.BoolProperty(name="is_create_driver_parent_transmitter", description="If driver target is new or specific, add transmitter of original parent bone's transform.", default=False, subtype="NONE")
    driver_parent_transmitter_identifier: bpy.props.StringProperty(name="driver_parent_transmitter_identifier", description="Driver parent transmitter's prefix or suffix", default="transmit", subtype="NONE")

    # Bendy bone properties(editbone)
    segments: bpy.props.IntProperty(name="segments", description="Bendy bone segments", default=16, min=1, max=32, soft_min=1, soft_max=32, step=1, subtype='NONE')
    curve_in_x: bpy.props.FloatProperty(name="curve_in_x", description="X-axis handle offset for start of the B-Bone's curve, adjusts curvature", default=0.0, step=0.01, subtype="NONE", precision=5)
    curve_out_x: bpy.props.FloatProperty(name="curve_out_x", description="X-axis handle offset for end of the B-Bone's curve, adjusts curvature", default=0.0, step=0.01, subtype="NONE", precision=5)
    curve_in_z: bpy.props.FloatProperty(name="curve_in_z", description="Z-axis handle offset for start of the B-Bone's curve, adjusts curvature", default=0.0, step=0.01, subtype="NONE", precision=5)
    curve_out_z: bpy.props.FloatProperty(name="curve_out_z", description="Z-axis handle offset for end of the B-Bone's curve, adjusts curvature", default=0.0, step=0.01, subtype="NONE", precision=5)
    scale_in_x: bpy.props.FloatProperty(name="scale_in_x", description="Scale factor for start of the B-Bone, adjusts thickness (for tapering effects)", default=1.0, step=0.01, subtype="NONE", precision=5)
    scale_in_y: bpy.props.FloatProperty(name="scale_in_y", description="Scale factor for start of the B-Bone, adjusts thickness (for tapering effects)", default=1.0, step=0.01, subtype="NONE", precision=5)
    scale_in_z: bpy.props.FloatProperty(name="scale_in_z", description="Scale factor for start of the B-Bone, adjusts thickness (for tapering effects)", default=1.0, step=0.01, subtype="NONE", precision=5)
    scale_out_x: bpy.props.FloatProperty(name="scale_out_x", description="Scale factor for end of the B-Bone, adjusts thickness (for tapering effects)", default=1.0, step=0.01, subtype="NONE", precision=5)
    scale_out_y: bpy.props.FloatProperty(name="scale_out_y", description="Scale factor for end of the B-Bone, adjusts thickness (for tapering effects)", default=1.0, step=0.01, subtype="NONE", precision=5)
    scale_out_z: bpy.props.FloatProperty(name="scale_out_z", description="Scale factor for end of the B-Bone, adjusts thickness (for tapering effects)", default=1.0, step=0.01, subtype="NONE", precision=5)
    roll_in: bpy.props.FloatProperty(name="roll_in", description="Roll offset for the start of the B-Bone, adjusts twist", default=0.0, step=1.0, subtype="ANGLE", precision=5)
    roll_out: bpy.props.FloatProperty(name="roll_out", description="Roll offset for the end of the B-Bone, adjusts twist", default=0.0, step=1.0, subtype="ANGLE", precision=5)
    ease_in: bpy.props.FloatProperty(name="ease_in", description="Length of first Bezier Handle (for B-Bones only)", default=1.0, step=0.01, min=0.0, max=2.0, soft_min=0.0, soft_max=2.0, subtype="NONE", precision=5)
    ease_out: bpy.props.FloatProperty(name="ease_out", description="Length of second Bezier Handle (for B-Bones only)", default=1.0, step=0.01, min=0.0, max=2.0, soft_min=0.0, soft_max=2.0, subtype="NONE", precision=5)
    ease_in_pose: bpy.props.FloatProperty(name="ease_in", description="Length of first Bezier Handle (for B-Bones only)", default=0.0, step=0.01, min=0.0, max=2.0, soft_min=0.0, soft_max=2.0, subtype="NONE", precision=5)
    ease_out_pose: bpy.props.FloatProperty(name="ease_out", description="Length of second Bezier Handle (for B-Bones only)", default=0.0, step=0.01, min=0.0, max=2.0, soft_min=0.0, soft_max=2.0, subtype="NONE", precision=5)

    # Bendy bone properties(posebone)
    constraints_bulge: bpy.props.FloatProperty(name="constraints_bulge", description='"Stretch to" constraints volume value.volume="1.0":If bbone squashed,inflate/"0.0":not inflate', default=0.0, step=0.1, subtype="NONE")

    # Bendy bone pose properties
    is_insert_keyframes: bpy.props.BoolProperty(name="is_insert_keyframes", description="Insert keyframes of bbones curve after confirm.", default=False, subtype="NONE")

    # For rename bones properties
    rename_bones_grp: bpy.props.CollectionProperty(type=RenameBoneItemsPropGrp)
    rename_bones_grp_idx: bpy.props.IntProperty()
    rename_bones_basename: bpy.props.StringProperty(name="rename_bones_basename", description="Base name of bones.", default="Name", subtype='NONE')
    rename_bones_separator: bpy.props.StringProperty(name="rename_bones_separator", description="Separator of parts of name.", default="_", subtype="NONE")
    rename_bones_padding_num: bpy.props.IntProperty(name="rename_bones_padding_num", description="Padding number of digits.", default=1, min=1, max=6, soft_min=1, soft_max=6, step=1, subtype="NONE")
    rename_bones_incremental_type_it = []
    rename_bones_incremental_type_it.append((_RENAME_BONES_INCREMENTAL_TYPE_NONE, _RENAME_BONES_INCREMENTAL_TYPE_NONE, "Incremental character is none.", "", 1))
    rename_bones_incremental_type_it.append((_RENAME_BONES_INCREMENTAL_TYPE_ALPHA, _RENAME_BONES_INCREMENTAL_TYPE_ALPHA, "Incremental character is alphabet.", "", 2))
    rename_bones_incremental_type_it.append((_RENAME_BONES_INCREMENTAL_TYPE_NUMBER, _RENAME_BONES_INCREMENTAL_TYPE_NUMBER, "Incremental character is number.", "", 3))
    rename_bones_incremental_type: bpy.props.EnumProperty(items=rename_bones_incremental_type_it, default=_RENAME_BONES_INCREMENTAL_TYPE_ALPHA)
    rename_bones_incremental_offset: bpy.props.IntProperty(name="rename_bones_incremental_offset", description="Offset of start of numbering.", default=0, min=0, soft_min=0, step=1, subtype="NONE")
    rename_bones_is_mirror: bpy.props.BoolProperty(name="rename_bones_is_mirror", description="Rename X-Axis Mirror Bone.", default=True, subtype='NONE', update=_updateRenameXAxisMirror)
    rename_bones_letters_case_type_id = []
    rename_bones_letters_case_type_id.append((_RENAME_BONES_ALPHABET_CASE_UPPER, _RENAME_BONES_ALPHABET_CASE_UPPER, "Uppercase alphabets.", "", 0))
    rename_bones_letters_case_type_id.append((_RENAME_BONES_ALPHABET_CASE_LOWER, _RENAME_BONES_ALPHABET_CASE_LOWER, "Lowercase alphabets.", "", 1))
    rename_bones_letters_case_type: bpy.props.EnumProperty(items=rename_bones_letters_case_type_id, default=_RENAME_BONES_ALPHABET_CASE_UPPER)


def _defProperties():

    # Define Addon's Properties
    bpy.types.WindowManager.uil_setup_bendy_bone_auto_propgrp = bpy.props.PointerProperty(type=SetupBendyBoneProperties)


#########################################################
# Functions(Private)
#########################################################


def _getSelectedPoseBones(pbones, isMirror):

    ret = {}

    if not pbones:
        return ret

    for bone in pbones:

        if not common.isVisiblePoseBone(bone):
            continue

        if bone.bone.select:
            elm = common.getNameElements(bone)
            ret[bone] = elm

            if elm.isMirror and isMirror:

                mirrBoneNm = elm.mirror_bonename
                if mirrBoneNm in pbones.keys():

                    mirrbone = pbones[mirrBoneNm]
                    if mirrbone not in ret:
                        ret[mirrbone] = common.getNameElements(mirrbone)

    return ret


def _getSelectedEditableBones(editbones, isMirror):

    ret = {}

    if not editbones:
        return ret

    for bone in editbones:

        if not common.isVisibleBone(bone):
            continue

        if bone.select or bone.select_head or bone.select_tail:
            elm = common.getNameElements(bone)
            ret[bone] = elm

            if elm.isMirror and isMirror:

                mirrBoneNm = elm.mirror_bonename
                if mirrBoneNm in editbones.keys():

                    mirrbone = editbones[mirrBoneNm]
                    if mirrbone not in ret:
                        ret[mirrbone] = common.getNameElements(mirrbone)

    return ret


class TempParentHandle:

    TYPE_HEAD_2_TAIL = 2
    TYPE_TAIL_2_HEAD = 3

    bone = None
    type = -1

    def __init__(self, bone, type):
        self.bone = bone
        self.type = type


def _getDirectionVector(editbone):

    headVec = editbone.head.copy()
    tailVec = editbone.tail.copy()
    dVech2t = tailVec - headVec
    dVect2h = headVec - tailVec

    return (headVec, tailVec, dVech2t, dVect2h)


#########################################################
# Actions
#########################################################


class SetupBendyBoneAuto(bpy.types.Operator):
    '''
      Setup bendy bone
    '''
    bl_idname = "uiler.setupbendyboneauto"
    bl_label = "Setup Bendy Bone"
    bl_options = {'REGISTER', 'UNDO'}

    _const_temp = {}  # key:bone value:constraints
    _base_vec_map = {}  # key:Vector(head/tail) value:(basebone(with head), basebone(with tail), handle bone collection(head), handle bone collection(tail))
    _init_Armature = None
    _drv_target_Armature = None
    _new_Armature = None

    def _clearMyConstraints(self):

        for bone in self._const_temp.keys():
            bone.constraints.remove(self._const_temp[bone])

        self._const_temp = {}

    def _constructHandleBoneName(self, elm, hdl_id, end_id):

        ret = ""
        sep = "_"
        # lr_id = elm.lr_id
        # num = elm.numid
        isPrefix = elm.isPrefix
        # isSuffix = elm.isSuffix

        if isPrefix:
            ret = elm.bonename + sep + hdl_id + sep + end_id
        else:  # Suffix
            ret = hdl_id + sep + end_id + sep + elm.bonename

        return ret

    def _constructDriverHandleBoneName(self, elm, hdl_id, drv_id):

        ret = ""
        sep = "_"
        # lr_id = elm.lr_id
        # num = elm.numid
        isPrefix = elm.isPrefix
        # isSuffix = elm.isSuffix
        if isPrefix:
            ret = elm.bonename + sep + hdl_id + sep + drv_id
        else:  # Suffix
            ret = hdl_id + sep + drv_id + sep + elm.bonename

        return ret

    def _default2Active(self, propgrp, editbone):

        propgrp.bbone_scale_ratio = editbone.bbone_x * editbone.length
        propgrp.segments = editbone.bbone_segments
        propgrp.curve_in_x = editbone.bbone_curveinx
        propgrp.curve_out_x = editbone.bbone_curveoutx
        propgrp.curve_in_z = editbone.bbone_curveinz
        propgrp.curve_out_z = editbone.bbone_curveoutz
        propgrp.scale_in_x = editbone.bbone_scalein[0]
        propgrp.scale_in_y = editbone.bbone_scalein[1]
        propgrp.scale_in_z = editbone.bbone_scalein[2]
        propgrp.scale_out_x = editbone.bbone_scaleout[0]
        propgrp.scale_out_y = editbone.bbone_scaleout[1]
        propgrp.scale_out_z = editbone.bbone_scaleout[2]
        propgrp.roll_in = editbone.bbone_rollin
        propgrp.roll_out = editbone.bbone_rollout
        propgrp.ease_in = editbone.bbone_easein
        propgrp.ease_out = editbone.bbone_easeout

    def _addParentHandles(self, context):

        map = self._base_vec_map
        editbones = context.active_object.data.edit_bones

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp
        is_spec_parent = propgrp.parents_bone_type == _PARENTS_BONE_TYPE_SPECIFIC
        spec_parent_bone_nm = propgrp.specific_parents_bone_target
        spec_parent_bone = None
        if is_spec_parent:
            if not common.isEmptyStr(spec_parent_bone_nm):
                spec_parent_bone = editbones[spec_parent_bone_nm]

        for keyVec in map.keys():

            baseHList = sorted(map[keyVec][0])
            baseTList = sorted(map[keyVec][1])
            hdlHList = sorted(map[keyVec][2])
            hdlTList = sorted(map[keyVec][3])

            baseA = None
            if len(baseHList) > 0:
                baseA = TempParentHandle(editbones[baseHList[0]], TempParentHandle.TYPE_TAIL_2_HEAD)
            baseB = None
            if len(baseTList) > 0:
                baseB = TempParentHandle(editbones[baseTList[0]], TempParentHandle.TYPE_HEAD_2_TAIL)
            hdlH = None

            if not baseA and len(baseTList) > 1:
                baseA = TempParentHandle(editbones[baseTList[1]], TempParentHandle.TYPE_HEAD_2_TAIL)

            if not baseB and len(baseHList) > 1:
                baseB = TempParentHandle(editbones[baseHList[1]], TempParentHandle.TYPE_TAIL_2_HEAD)

            if len(hdlHList) > 0:
                hdlH = editbones[hdlHList[0]]
            hdlT = None
            if len(hdlTList) > 0:
                hdlT = editbones[hdlTList[0]]

            hashStrH = ""
            lr_id_h = ""
            lr_id_t = ""
            isLeft_a = False
            isLeft_b = False
            isRight_a = False
            isRight_b = False
            isPrefix_a = False
            isPrefix_b = False
            isSuffix_a = False
            isSuffix_b = False
            if baseA:
                elm = common.getNameElements(baseA.bone)
                hashStrH = common.constructBoneName(elm.basename_nonLR, "", elm.numid, elm.isPrefix, elm.isSuffix)
                lr_id_h = elm.lr_id
                isLeft_a = elm.isLeft
                isRight_a = elm.isRight
                isPrefix_a = elm.isPrefix
                isSuffix_a = elm.isSuffix

            hashStrT = ""
            if baseB:
                elm = common.getNameElements(baseB.bone)
                hashStrT = common.constructBoneName(elm.basename_nonLR, "", elm.numid, elm.isPrefix, elm.isSuffix)
                lr_id_t = elm.lr_id
                isLeft_b = elm.isLeft
                isRight_b = elm.isRight
                isPrefix_b = elm.isPrefix
                isSuffix_b = elm.isSuffix

            lr_id = ""
            if isLeft_a or isLeft_b or isRight_a or isRight_b:
                lr_id = lr_id_h
                if not baseA:
                    lr_id = lr_id_t

            if (isLeft_a and isRight_b) or (isLeft_b and isRight_a):
                lr_id = ""

            if (not isLeft_a) and (not isRight_a) and baseA:
                lr_id = ""

            if (not isLeft_b) and (not isRight_b) and baseB:
                lr_id = ""

            hdlNmBase = hashlib.md5((hashStrH + hashStrT).encode("utf-8")).hexdigest()
            hdlNm = common.constructBoneName(hdlNmBase, lr_id, "", isPrefix_a or isPrefix_b, isSuffix_a or isSuffix_b)

            is_hdl_already = False
            hdlBone = None
            if hdlNm in editbones.keys():
                is_hdl_already = True
                hdlBone = editbones[hdlNm]
            else:
                hdlBone = editbones.new(hdlNm)

            is_cross = False
            if baseA and baseB:
                is_cross = True

            if is_cross:

                length = 0
                parent = None
                bbone_x = 0
                bbone_z = 0
                if hdlT:
                    length = hdlT.length
                    parent = hdlT.parent
                    bbone_x = hdlT.bbone_x
                    bbone_z = hdlT.bbone_z

                if hdlH:
                    length = hdlH.length
                    parent = hdlH.parent
                    bbone_x = hdlH.bbone_x
                    bbone_z = hdlH.bbone_z

                # set vector
                baseVec = keyVec
                dirVec_h = _getDirectionVector(baseA.bone)[baseA.type]
                dirVec_t = _getDirectionVector(baseB.bone)[baseB.type]
                dirVec = dirVec_h.normalized() + dirVec_t.normalized()

                hdlBone.head = baseVec
                hdlBone.tail = baseVec + dirVec
                hdlBone.align_roll(baseB.bone.y_axis.copy())
                hdlBone.length = length
                hdlBone.bbone_x = bbone_x
                hdlBone.bbone_z = bbone_z
                hdlBone.select = False
                hdlBone.select_head = False
                hdlBone.select_tail = False

                # set parents
                if not is_hdl_already:

                    hdlBone.parent = parent
                    for boneNm in hdlHList:
                        editbones[boneNm].parent = hdlBone

                    for boneNm in hdlTList:
                        editbones[boneNm].parent = hdlBone

                elif is_hdl_already and is_spec_parent:

                    hdlBone.parent = spec_parent_bone
                    for boneNm in hdlHList:
                        editbones[boneNm].parent = hdlBone

                    for boneNm in hdlTList:
                        editbones[boneNm].parent = hdlBone

            else:

                pass

    def invoke(self, context, event):

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        # use value of active bone
        if propgrp.is_use_active_value:
            self._default2Active(propgrp, context.active_bone)

        return self.execute(context)

    def initTargetObject(self, context):

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        # initialize driver handle target armature
        self._init_Armature = context.active_object.name
        bpy.data.objects[self._init_Armature].data.display_type = "BBONE"
        if propgrp.is_add_driver_handle:

            if propgrp.add_driver_type == _ADD_DRIVER_TYPE_SELF:

                self._drv_target_Armature = context.active_object.name

            elif propgrp.add_driver_type == _ADD_DRIVER_TYPE_NEW_ARMATRUE:

                if common.isEmptyStr(propgrp.new_name_for_driver_target):
                    self.report({'ERROR_INVALID_INPUT'}, "Input new armature name.")
                    return {'CANCELLED'}

                armDt = bpy.data.armatures.new(propgrp.new_name_for_driver_target)
                newObj = bpy.data.objects.new(propgrp.new_name_for_driver_target, armDt)
                context.scene.collection.objects.link(newObj)
                self._new_Armature = newObj.name

                self._drv_target_Armature = self._new_Armature

            elif propgrp.add_driver_type == _ADD_DRIVER_TYPE_SPECIFIC:

                if common.isEmptyStr(propgrp.specific_add_driver_target):
                    self.report({'ERROR_INVALID_INPUT'}, "Input target armature.")
                    return {'CANCELLED'}
                target_obj = bpy.data.objects[propgrp.specific_add_driver_target]

                if target_obj.type != "ARMATURE":
                    self.report({'ERROR_INVALID_INPUT'}, "Input Armature.")
                    return {'CANCELLED'}

                if target_obj == bpy.data.objects[self._init_Armature]:
                    self.report({'ERROR_INVALID_INPUT'}, "Input another Armature.")
                    return {'CANCELLED'}

                self._drv_target_Armature = target_obj.name

            bpy.data.objects[self._drv_target_Armature].data.display_type = "BBONE"

    def execute(self, context):

        self.initTargetObject(context)

        # Initialize for loop call #
        # self._clearMyConstraints()
        self._base_vec_map = {}

        obj = context.active_object
        editbones = obj.data.edit_bones
        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp
        is_edit_curve = propgrp.is_edit_curve
        is_add_handles = propgrp.is_add_handles
        is_spec_parent = propgrp.parents_bone_type == _PARENTS_BONE_TYPE_SPECIFIC
        spec_parent_bone_nm = propgrp.specific_parents_bone_target
        spec_parent_bone = None
        if is_spec_parent:
            if not common.isEmptyStr(spec_parent_bone_nm):
                spec_parent_bone = editbones[spec_parent_bone_nm]

        targetEditBones = _getSelectedEditableBones(editbones, propgrp.is_mirror)
        targetBoneNms = []
        drvHdlInfos = []
        bone_thin = propgrp.bbone_scale
        # EDIT MODE PROCESS #
        for editbone in targetEditBones.keys():  # key:bpy.types.EditBone value:@see common.getNameElements(bone).returnValue

            is_hdl_already = False
            hdl_id = propgrp.handle_identifier
            tail_id = propgrp.tail_identifier
            head_id = propgrp.head_identifier
            drv_in_id = propgrp.driver_handle_in_identifier
            drv_out_id = propgrp.driver_handle_out_identifier
            elm = targetEditBones[editbone]
#             bone_thin = 1 / editbone.length * propgrp.bbone_scale_ratio

            # add handle bone #
            vec = _getDirectionVector(editbone)
            baseVec_h = vec[0].freeze()
            baseVec_t = vec[1].freeze()
            baseVec_h2t = vec[2].freeze()
            baseVec_t2h = vec[3].freeze()
            tpar = 1.0 + propgrp.handle_size_ratio
            if is_add_handles:

                editbone.use_connect = False

                # head/tail handle #
                hdl_head_nm = self._constructHandleBoneName(elm, hdl_id, head_id)
                if hdl_head_nm not in editbones.keys():
                    editbone_h = editbones.new(hdl_head_nm)
                else:
                    is_hdl_already = True
                    editbone_h = editbones[hdl_head_nm]
#                 editbone_h.head = baseVec_t + tpar * baseVec_t2h # new head = tailVec + tpar * "direction vector(tail -> head)"
#                 editbone_h.tail = baseVec_h
                editbone_h.head = baseVec_h
                editbone_h.tail = baseVec_t + tpar * baseVec_t2h  # new head = tailVec + tpar * "direction vector(tail -> head)"
                editbone_h.length = propgrp.handle_size
                tmpTail = editbone_h.head.copy()
                tmpHead = editbone_h.tail.copy()
                editbone_h.head = tmpHead
                editbone_h.tail = tmpTail
                editbone_h.roll = editbone.roll
                editbone_h.select = False
                editbone_h.select_head = False
                editbone_h.select_tail = False

                hdl_tail_nm = self._constructHandleBoneName(elm, hdl_id, tail_id)
                if hdl_tail_nm not in editbones.keys():
                    editbone_t = editbones.new(hdl_tail_nm)
                else:
                    is_hdl_already = True
                    editbone_t = editbones[hdl_tail_nm]
                editbone_t.head = baseVec_t
                editbone_t.tail = baseVec_h + tpar * baseVec_h2t  # new tail = headVec + tpar * "direction vector(head -> tail)"
                editbone_t.roll = editbone.roll
                editbone_t.length = propgrp.handle_size
                editbone_t.select = False
                editbone_t.select_head = False
                editbone_t.select_tail = False

                # set handle
                editbone.bbone_handle_type_start = 'ABSOLUTE'
                editbone.bbone_handle_type_end = 'ABSOLUTE'
                editbone.bbone_custom_handle_start = editbone_h
                editbone.bbone_custom_handle_end = editbone_t

                # head
                pHdlVal_h = ([], [], [], [])
                if baseVec_h in self._base_vec_map.keys():
                    pHdlVal_h = self._base_vec_map[baseVec_h]

                pHdlVal_h[0].append(editbone.name)
                pHdlVal_h[2].append(editbone_h.name)

                self._base_vec_map[baseVec_h] = pHdlVal_h

                # tail
                pHdlVal_t = ([], [], [], [])
                if baseVec_t in self._base_vec_map.keys():
                    pHdlVal_t = self._base_vec_map[baseVec_t]

                pHdlVal_t[1].append(editbone.name)
                pHdlVal_t[3].append(editbone_t.name)

                self._base_vec_map[baseVec_t] = pHdlVal_t

                # driver handle(create info list) #
                align_roll_vec = editbone.y_axis.copy()
                align_roll_vec.negate()

                drv_hdl_in = DriverHandleBoneInfo()
                drv_hdl_in_nm = self._constructDriverHandleBoneName(elm, hdl_id, drv_in_id)
                drv_hdl_in.name = drv_hdl_in_nm
                drv_hdl_in.driver_target_nm = editbone.name
                drv_hdl_in.align_roll_vec = align_roll_vec
                drv_hdl_in.head_vec = baseVec_h + baseVec_h2t * _DRIVER_HANDLE_LOC_OFFSET
                drv_hdl_in.tail_vec = drv_hdl_in.head_vec.copy() + editbone.z_axis.copy()
                drv_hdl_in.length = editbone_h.length * propgrp.driver_handle_size_ratio
                drv_hdl_in.bone_thin = bone_thin
                drv_hdl_in.inout_type = DriverHandleBoneInfo.INOUT_TYPE_IN
                drvHdlInfos.append(drv_hdl_in)

                drv_hdl_out = DriverHandleBoneInfo()
                drv_hdl_out_nm = self._constructDriverHandleBoneName(elm, hdl_id, drv_out_id)
                drv_hdl_out.name = drv_hdl_out_nm
                drv_hdl_out.driver_target_nm = editbone.name
                drv_hdl_out.align_roll_vec = align_roll_vec
                drv_hdl_out.head_vec = baseVec_t + baseVec_t2h * _DRIVER_HANDLE_LOC_OFFSET
                drv_hdl_out.tail_vec = drv_hdl_out.head_vec.copy() + editbone.z_axis.copy()
                drv_hdl_out.length = editbone_t.length * propgrp.driver_handle_size_ratio
                drv_hdl_out.bone_thin = bone_thin
                drv_hdl_out.inout_type = DriverHandleBoneInfo.INOUT_TYPE_OUT
                drvHdlInfos.append(drv_hdl_out)

                # parent handle #
                if not is_hdl_already:

                    parent = editbone.parent
                    if is_spec_parent:
                        parent = spec_parent_bone
                    editbone_h.parent = parent
                    editbone_t.parent = parent
                    editbone.parent = editbone_h

                    if parent:
                        drv_hdl_in.parentNm = drv_hdl_out.parentNm = parent.name
                        drv_hdl_in.parentVec_h = drv_hdl_out.parentVec_h = parent.head.copy()
                        drv_hdl_in.parentVec_t = drv_hdl_out.parentVec_t = parent.tail.copy()
                        drv_hdl_in.parentRoll = drv_hdl_out.parentRoll = parent.roll
                        drv_hdl_in.parentElm = drv_hdl_out.parentElm = common.getNameElements(
                            parent)

                elif is_hdl_already and is_spec_parent:

                    parent = spec_parent_bone
                    editbone_h.parent = parent
                    editbone_t.parent = parent
                    editbone.parent = editbone_h

                    if parent:
                        drv_hdl_in.parentNm = drv_hdl_out.parentNm = parent.name
                        drv_hdl_in.parentVec_h = drv_hdl_out.parentVec_h = parent.head.copy()
                        drv_hdl_in.parentVec_t = drv_hdl_out.parentVec_t = parent.tail.copy()
                        drv_hdl_in.parentRoll = drv_hdl_out.parentRoll = parent.roll
                        drv_hdl_in.parentElm = drv_hdl_out.parentElm = common.getNameElements(
                            parent)

                # Bendy bone setting(Editbone)
                editbone_h.bbone_x = editbone_t.bbone_x = bone_thin
                editbone_h.bbone_z = editbone_t.bbone_z = bone_thin

                targetBoneNms.append(
                    (editbone.name, editbone_h.name, editbone_t.name))

            # Bendy bone setting #
            if is_edit_curve:
                editbone.bbone_x = bone_thin
                editbone.bbone_z = bone_thin
                mirrParam = 1.0
                if elm.isMirror and elm.isRight:
                    mirrParam = -1.0
                editbone.bbone_segments = propgrp.segments
                editbone.bbone_curveinx = propgrp.curve_in_x * mirrParam
                editbone.bbone_curveoutx = propgrp.curve_out_x * mirrParam
                editbone.bbone_curveinz = propgrp.curve_in_z
                editbone.bbone_curveoutz = propgrp.curve_out_z
                editbone.bbone_scalein[0] = propgrp.scale_in_x
                editbone.bbone_scalein[1] = propgrp.scale_in_y
                editbone.bbone_scalein[2] = propgrp.scale_in_z
                editbone.bbone_scaleout[0] = propgrp.scale_out_x
                editbone.bbone_scaleout[1] = propgrp.scale_out_y
                editbone.bbone_scaleout[2] = propgrp.scale_out_z
                editbone.bbone_rollin = propgrp.roll_in * mirrParam
                editbone.bbone_rollout = propgrp.roll_out * mirrParam
                editbone.bbone_easein = propgrp.ease_in
                editbone.bbone_easeout = propgrp.ease_out

        # parent head/tail handle #
        if propgrp.is_create_parent_of_handles:
            self._addParentHandles(context)

        # driver handle(actually create) #
        if propgrp.is_add_driver_handle:
            self._createDriverHandle(context, drvHdlInfos)

        if propgrp.is_add_driver_handle:
            self._addDrivers(context, drvHdlInfos)

        # POSE MODE PROCESS #
        bpy.ops.object.mode_set(mode='POSE', toggle=True)
        self._createStretchToConstraints(context, obj, targetBoneNms)

        bpy.ops.object.mode_set(mode='EDIT', toggle=True)

        return {'FINISHED'}

    def _addDrivers(self, context, infos):

        obj = context.active_object

        for drvinf in infos:
            self._initDriverBase(obj, 'pose.bones["' + drvinf.driver_target_nm + '"].bbone_curve' + drvinf.inout_type + 'x', drvinf, "LOC_X")
            self._initDriverBase(obj, 'pose.bones["' + drvinf.driver_target_nm + '"].bbone_curve' + drvinf.inout_type + 'z', drvinf, "LOC_Y")
            self._initDriverBase(obj, 'pose.bones["' + drvinf.driver_target_nm + '"].bbone_scale' + drvinf.inout_type, drvinf, "SCALE_X", 0)
            self._initDriverBase(obj, 'pose.bones["' + drvinf.driver_target_nm + '"].bbone_scale' + drvinf.inout_type, drvinf, "SCALE_Y", 1)
            self._initDriverBase(obj, 'pose.bones["' + drvinf.driver_target_nm + '"].bbone_scale' + drvinf.inout_type, drvinf, "SCALE_Z", 2)
            self._initDriverBase(obj, 'pose.bones["' + drvinf.driver_target_nm + '"].bbone_roll' + drvinf.inout_type, drvinf, "ROT_Z").expression = "-var"

    def _initDriverBase(self, obj, data_path, drvinf, transType, data_idx=-1):

        obj.driver_remove(data_path, data_idx)
        driver = obj.driver_add(data_path, data_idx).driver
        driver.type = "SCRIPTED"
        driver.expression = "var"

        v = driver.variables.new()
        v.name = "var"
        v.type = "TRANSFORMS"
        v.targets[0].id = bpy.data.objects[self._drv_target_Armature]
        v.targets[0].bone_target = drvinf.name
        v.targets[0].transform_type = transType
        v.targets[0].transform_space = "TRANSFORM_SPACE"

        return driver

    def _createStretchToConstraints(self, context, obj, targetBoneNms):

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        for names in targetBoneNms:

            bones = obj.pose.bones
            bone = bones[names[0]]
            # bone_h = bones[names[1]]
            bone_t = bones[names[2]]

            if _CONSTRAINTS_NAME_STRETCH_TO in bone.constraints.keys():
                const = bone.constraints[_CONSTRAINTS_NAME_STRETCH_TO]
            else:
                const = bone.constraints.new("STRETCH_TO")
                const.name = _CONSTRAINTS_NAME_STRETCH_TO
            const.target = obj
            const.subtarget = bone_t.name
            const.rest_length = bone.length
            const.bulge = propgrp.constraints_bulge
            self._const_temp[bone] = const

    def _createDriverHandle(self, context, infos):

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        if propgrp.add_driver_type != _ADD_DRIVER_TYPE_SELF:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            context.view_layer.objects.active = bpy.data.objects[self._drv_target_Armature]
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        obj = context.active_object
        editbones = obj.data.edit_bones

        is_spec_parent = propgrp.parents_bone_type == _PARENTS_BONE_TYPE_SPECIFIC
        spec_parent_bone_nm = propgrp.specific_parents_bone_target
        spec_parent_bone = None
        if is_spec_parent:
            if not common.isEmptyStr(spec_parent_bone_nm) and spec_parent_bone_nm in editbones.keys():
                spec_parent_bone = editbones[spec_parent_bone_nm]

        is_hdl_already = False
        parentsDic = {}
        for drvinf in infos:

            drv_hdl_nm = drvinf.name
            if drv_hdl_nm not in editbones.keys():
                drvbone = editbones.new(drv_hdl_nm)
            else:
                is_hdl_already = True
                drvbone = editbones[drv_hdl_nm]

            drvbone.head = drvinf.head_vec
            drvbone.tail = drvinf.tail_vec
            drvbone.align_roll(drvinf.align_roll_vec)
            drvbone.length = drvinf.length
            drvbone.bbone_x = drvinf.bone_thin
            drvbone.bbone_z = drvinf.bone_thin
            drvbone.select = False
            drvbone.select_head = False
            drvbone.select_tail = False

            if is_hdl_already:
                pass
            else:
                if not common.isEmptyStr(drvinf.parentNm) and drvinf.parentNm in editbones.keys():
                    drvbone.parent = editbones[drvinf.parentNm]

            if is_spec_parent:
                drvbone.parent = spec_parent_bone

            if propgrp.is_create_driver_parent_transmitter and (propgrp.add_driver_type != _ADD_DRIVER_TYPE_SELF):
                transmitter_elm = drvinf.parentElm
                transmitter_id = propgrp.driver_parent_transmitter_identifier
                if transmitter_elm:
                    if transmitter_elm.isPrefix:
                        transmitter_nm = drvinf.parentNm + "_" + transmitter_id
                    else:  # Suffix
                        transmitter_nm = transmitter_id + "_" + drvinf.parentNm

                    if transmitter_nm in editbones.keys():
                        transmitter = editbones[transmitter_nm]
                    else:
                        transmitter = editbones.new(transmitter_nm)
                        transmitter.head = drvinf.parentVec_h
                        transmitter.tail = drvinf.parentVec_t
                        transmitter.roll = drvinf.parentRoll

                    drvbone.parent = transmitter
                    parentsDic[transmitter_nm] = transmitter_elm
                    transmitter.select = False
                    transmitter.select_head = False
                    transmitter.select_tail = False

        # Set Copy Transform constraints #
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        context.view_layer.objects.active = bpy.data.objects[self._init_Armature]
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        posebones = context.active_object.pose.bones
        for transmitter_nm in parentsDic.keys():
            parentElm = parentsDic[transmitter_nm]
            parents = posebones[parentElm.bonename]
            for const in parents.constraints:
                if const.name == _TRANSMITTER_CONSTRAINTS_NAME:
                    parents.constraints.remove(const)
                    break

            const = parents.constraints.new("COPY_TRANSFORMS")
            const.name = _TRANSMITTER_CONSTRAINTS_NAME
            const.target = obj
            const.subtarget = transmitter_nm

        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        # back to init Armature Object
        if propgrp.add_driver_type != _ADD_DRIVER_TYPE_SELF:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            context.view_layer.objects.active = bpy.data.objects[self._init_Armature]
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    def draw(self, context):

        layout = self.layout
        box = layout.box()
        box.label(text="Bendy Bone Setting")
        col = box.column()

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp
        is_edit_curve = propgrp.is_edit_curve

        col.prop(propgrp, "bbone_scale")
        col.prop(propgrp, "handle_size")
        col.prop(propgrp, "driver_handle_size_ratio")

        if is_edit_curve:
            col.prop(propgrp, "segments")
            col.prop(propgrp, "curve_in_x")
            col.prop(propgrp, "curve_out_x")
            col.prop(propgrp, "curve_in_z")
            col.prop(propgrp, "curve_out_z")
            col.prop(propgrp, "scale_in_x")
            col.prop(propgrp, "scale_in_y")
            col.prop(propgrp, "scale_in_z")
            col.prop(propgrp, "scale_out_x")
            col.prop(propgrp, "scale_out_y")
            col.prop(propgrp, "scale_out_z")
            col.prop(propgrp, "roll_in")
            col.prop(propgrp, "roll_out")
            col.prop(propgrp, "ease_in")
            col.prop(propgrp, "ease_out")

        col.prop(propgrp, "constraints_bulge", text="Volume Variation")


class TransformBendyBoneForPose(bpy.types.Operator):
    '''
      Transform pose bones
    '''
    bl_idname = "uiler.transformbendyboneforpose"
    bl_label = "Setup Bendy Bone"
    bl_options = {'REGISTER', 'UNDO'}

    def _default2Active(self, propgrp, pbone):

        propgrp.curve_in_x = pbone.bbone_curveinx
        propgrp.curve_out_x = pbone.bbone_curveoutx
        propgrp.curve_in_z = pbone.bbone_curveinz
        propgrp.curve_out_z = pbone.bbone_curveoutz
        propgrp.scale_in_x = pbone.bbone_scalein[0]
        propgrp.scale_in_y = pbone.bbone_scalein[1]
        propgrp.scale_in_z = pbone.bbone_scalein[2]
        propgrp.scale_out_x = pbone.bbone_scaleout[0]
        propgrp.scale_out_y = pbone.bbone_scaleout[1]
        propgrp.scale_out_z = pbone.bbone_scaleout[2]
        propgrp.roll_in = pbone.bbone_rollin
        propgrp.roll_out = pbone.bbone_rollout
        propgrp.ease_in_pose = pbone.bbone_easein
        propgrp.ease_out_pose = pbone.bbone_easeout

    def invoke(self, context, event):

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        if propgrp.is_use_active_value:
            self._default2Active(propgrp, context.active_pose_bone)

        obj = context.active_object
        pbones = obj.pose.bones
        targetPoseBones = _getSelectedPoseBones(pbones, propgrp.is_mirror)

        global _insertKeyfrmPboneList
        _insertKeyfrmPboneList = []
        for bone in targetPoseBones.keys():
            _insertKeyfrmPboneList.append(bone.name)

        return self.execute(context)

    def execute(self, context):

        # Initialize for loop call #
        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        obj = context.active_object
        scn = context.scene
        frm = scn.frame_current
        anm = obj.animation_data
        if propgrp.is_insert_keyframes:

            if not anm:
                anm = obj.animation_data_create()

            act = anm.action
            if not act:
                anm.action = act = bpy.data.actions.new(obj.name + " Action")

        pbones = obj.pose.bones
        targetPoseBones = _getSelectedPoseBones(pbones, propgrp.is_mirror)
        # EDIT MODE PROCESS #
        for pbone in targetPoseBones.keys():

            elm = targetPoseBones[pbone]

            # Bendy bone setting(Editbone)
            mirrParam = 1.0
            if elm.isMirror and elm.isRight:
                mirrParam = -1.0
            pbone.bbone_curveinx = propgrp.curve_in_x * mirrParam
            pbone.bbone_curveoutx = propgrp.curve_out_x * mirrParam
            pbone.bbone_curveinz = propgrp.curve_in_z
            pbone.bbone_curveoutz = propgrp.curve_out_z
            pbone.bbone_scalein[0] = propgrp.scale_in_x
            pbone.bbone_scalein[1] = propgrp.scale_in_y
            pbone.bbone_scalein[2] = propgrp.scale_in_z
            pbone.bbone_scaleout[0] = propgrp.scale_out_x
            pbone.bbone_scaleout[1] = propgrp.scale_out_y
            pbone.bbone_scaleout[2] = propgrp.scale_out_z
            pbone.bbone_rollin = propgrp.roll_in * mirrParam
            pbone.bbone_rollout = propgrp.roll_out * mirrParam
            pbone.bbone_easein = propgrp.ease_in_pose
            pbone.bbone_easeout = propgrp.ease_out_pose

            if propgrp.is_insert_keyframes:

                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_curveinx', pbone.bbone_curveinx)
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_curveinz', pbone.bbone_curveinz)
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_curveoutx', pbone.bbone_curveoutx)
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_curveoutz', pbone.bbone_curveoutz)
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_scalein[0]', pbone.bbone_scalein[0])
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_scalein[1]', pbone.bbone_scalein[1])
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_scalein[2]', pbone.bbone_scalein[2])
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_scaleout[0]', pbone.bbone_scaleout[0])
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_scaleout[1]', pbone.bbone_scaleout[1])
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_scaleout[2]', pbone.bbone_scaleout[2])
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_rollin', pbone.bbone_rollin)
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_rollout', pbone.bbone_rollout)
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_easein', pbone.bbone_easein)
                self._insertKeyFrame(frm, act, 'pose.bones["' + pbone.name + '"].bbone_easeout', pbone.bbone_easeout)

        return {'FINISHED'}

    def draw(self, context):

        layout = self.layout
        box = layout.box()
        box.label(text="Bendy Bone Setting")
        col = box.column()

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp
        col.prop(propgrp, "curve_in_x")
        col.prop(propgrp, "curve_out_x")
        col.prop(propgrp, "curve_in_z")
        col.prop(propgrp, "curve_out_z")
        col.prop(propgrp, "scale_in_x")
        col.prop(propgrp, "scale_in_y")
        col.prop(propgrp, "scale_in_z")
        col.prop(propgrp, "scale_out_x")
        col.prop(propgrp, "scale_out_y")
        col.prop(propgrp, "scale_out_z")
        col.prop(propgrp, "roll_in")
        col.prop(propgrp, "roll_out")
        col.prop(propgrp, "ease_in_pose")
        col.prop(propgrp, "ease_out_pose")
        col.prop(propgrp, "is_insert_keyframes", text="Insert keyframes", icon="REC", toggle=True)
        col.operator("uiler.bendyboneposeconfirmoperation", text="Confirm", icon="FILE_TICK")

    def _insertKeyFrame(self, frm, act, data_path, value):

        fc = act.fcurves.find(data_path, index=0)
        if not fc:
            fc = act.fcurves.new(data_path)
        fc.keyframe_points.insert(frm, value)


_insertKeyfrmPboneList = None


class BendyBonePoseConfirmOperation(bpy.types.Operator):
    bl_idname = "uiler.bendyboneposeconfirmoperation"
    bl_label = "Setup Bendy Bone(Confirm)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        return {'FINISHED'}


def _reNumberPropIdx(context):
    '''
      Rename by order
    '''

    propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp
    list = propgrp.rename_bones_grp

    for idx in range(0, len(list)):
        list[idx].idx = idx

    pass


def _chkExistRenameTargetBone(context, bone):

    propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

    for item in propgrp.rename_bones_grp:
        if item.name == bone.name:
            return True

        if propgrp.rename_bones_is_mirror:
            elm = common.getNameElements(bone)
            if item.name == elm.mirror_bonename:
                return True

    return False


class AddFunction(bpy.types.Operator):
    bl_idname = "uiler.addrenamebonesbyorderatbendybonesetupauto"
    bl_label = "label"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        for bone in context.selected_pose_bones:
            if _chkExistRenameTargetBone(context, bone):
                continue
            item = propgrp.rename_bones_grp.add()
            item.id = len(propgrp.rename_bones_grp)
            item.name = bone.name
            propgrp.rename_bones_grp_idx = len(propgrp.rename_bones_grp) - 1

            _reNumberPropIdx(context)

        return {'FINISHED'}


class RemoveFunction(bpy.types.Operator):
    bl_idname = "uiler.removerenamebonesbyorderatbendybonesetupauto"
    bl_label = "label"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        idx = propgrp.rename_bones_grp_idx
        propgrp.rename_bones_grp.remove(idx)

        _reNumberPropIdx(context)

        return {'FINISHED'}


class UpFunction(bpy.types.Operator):
    bl_idname = "uiler.uprenamebonesbyorderatbendybonesetupauto"
    bl_label = "label"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        idx = propgrp.rename_bones_grp_idx

        if idx < 1:
            return {'FINISHED'}

        # length = len(propgrp.rename_bones_grp)
        propgrp.rename_bones_grp.move(idx, idx - 1)
        propgrp.rename_bones_grp_idx -= 1

        _reNumberPropIdx(context)

        return {'FINISHED'}


class DownFunction(bpy.types.Operator):
    bl_idname = "uiler.downrenamebonesbyorderatbendybonesetupauto"
    bl_label = "label"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        idx = propgrp.rename_bones_grp_idx
        length = len(propgrp.rename_bones_grp)

        if idx > length - 2:
            return {'FINISHED'}

        propgrp.rename_bones_grp.move(idx, idx + 1)
        propgrp.rename_bones_grp_idx += 1

        _reNumberPropIdx(context)

        return {'FINISHED'}


class RefreshFunction(bpy.types.Operator):
    bl_idname = "uiler.refreshrenamebonesbyorderatbendybonesetupauto"
    bl_label = "label"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        for item in propgrp.rename_bones_grp:
            propgrp.rename_bones_grp.remove(0)

        for bone in context.selected_pose_bones:
            if _chkExistRenameTargetBone(context, bone):
                continue
            item = propgrp.rename_bones_grp.add()
            item.id = len(propgrp.rename_bones_grp)
            item.name = bone.name

#         _reNumberPropIdx(context)

        return {'FINISHED'}


class RenameBoneInfo:

    bones = None
    name_element = None
    name_org = ""
    name_hash = ""
    name_new = ""
    bone = None
    is_mirror = False
    name_element_mirr = None
    bone_mirr = None
    name_org_mirr = ""
    name_hash_mirr = ""
    name_new_mirr = ""

    def __init__(self, bones, bone, is_mirror):
        self.bone = bone
        elm = self.name_element = common.getNameElements(bone)
        self.name_org = bone.name
        self.name_hash = hashlib.md5((bone.name).encode("utf-8")).hexdigest()
        self.is_mirror = is_mirror and elm.isMirror
        if self.is_mirror:
            self.name_org_mirr = elm.mirror_bonename
            if elm.mirror_bonename in bones.keys():
                self.bone_mirr = bones[elm.mirror_bonename]
                self.name_element_mirr = common.getNameElements(self.bone_mirr)
                self.name_hash_mirr = hashlib.md5((elm.mirror_bonename).encode("utf-8")).hexdigest()

    def rename2hash(self):
        self.bone.name = self.name_hash
        if self.is_mirror:
            self.bone_mirr.name = self.name_hash_mirr

        return self

    def setNameByBaseAndNumber(self, base, num, sep):

        elm = self.name_element
        baseNm = base
        if not common.isEmptyStr(num):
            baseNm = baseNm + sep + num

        self.name_new = self.bone.name = common.constructBoneName(baseNm, elm.lr_id, "", elm.isPrefix, elm.isSuffix)

        if self.is_mirror:
            elm = self.name_element_mirr
            self.name_new_mirr = self.bone_mirr.name = common.constructBoneName(baseNm, elm.lr_id, "", elm.isPrefix, elm.isSuffix)


class RenameBySelectedOrder(bpy.types.Operator):
    bl_idname = "uiler.renameselectedbonesbyorderatbendybonesetupauto"
    bl_label = "Rename by order"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        propgrp = context.window_manager.uil_setup_bendy_bone_auto_propgrp

        if common.isEmptyStr(propgrp.rename_bones_basename):
            self.report({'ERROR_INVALID_INPUT'}, "Input base name.")
            return {'FINISHED'}

        # bone name to hash
        is_mirror = propgrp.rename_bones_is_mirror
        bones = context.active_object.pose.bones
        remList = []
        for item in propgrp.rename_bones_grp:
            if item.name in bones.keys():
                remList.append(RenameBoneInfo(bones, bones[item.name], is_mirror).rename2hash())

        idx = propgrp.rename_bones_incremental_offset
        for boneInf in remList:
            num = ""
            if propgrp.rename_bones_incremental_type == _RENAME_BONES_INCREMENTAL_TYPE_ALPHA:
                num = common.getAlphabetByNumber(idx, propgrp.rename_bones_letters_case_type)

            if propgrp.rename_bones_incremental_type == _RENAME_BONES_INCREMENTAL_TYPE_NUMBER:
                num = common.getPaddingStringByDigit(idx, propgrp.rename_bones_padding_num)

            boneInf.setNameByBaseAndNumber(propgrp.rename_bones_basename, num, propgrp.rename_bones_separator)

            idx += 1

        return {'FINISHED'}


#########################################################
# UI
#########################################################


class SetupBendyBoneAutoUIForEdit(bpy.types.Panel):
    bl_label = "Setup Bendy Bone Auto"
    bl_idname = "UILER_SETUP_BENDY_BONE_AUTO_FOR_EDIT_UI_PT_layout"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SBB"
    bl_context = "armature_edit"

    @classmethod
    def poll(cls, context):
        return "OK"

    def draw(self, context):

        layout = self.layout
        propgrp = bpy.context.window_manager.uil_setup_bendy_bone_auto_propgrp

        box = layout.box()
        box.label(text="Setup Bendy Bone:", icon="TRIA_DOWN")
        row = box.row()
        col = row.column()
        col.operator("uiler.setupbendyboneauto", text="Setup", icon="PLAY")
        col.prop(propgrp, "is_mirror", text="X-Axis mirror", toggle=False)
        col.prop(propgrp, "is_use_active_value", text="Use active values", toggle=False)
        col.prop(propgrp, "is_edit_curve", text="Edit curve values", toggle=False)

        col.label(text="Parents settings:")
        box_p = col.box()
        col_p = box_p.column()
        col_p.prop(propgrp, "is_create_parent_of_handles", text="Add/Edit parent of handles", toggle=False)
        row = col_p.row(align=True)
        row.prop(propgrp, "parents_bone_type", expand=True)
        if propgrp.parents_bone_type == _PARENTS_BONE_TYPE_SPECIFIC:
            col_p.prop_search(propgrp, "specific_parents_bone_target", context.active_object.data, "edit_bones")

        col.label(text="Driver settings:")
        box_d = col.box()
        col_d = box_d.column()
        col_d.prop(propgrp, "is_add_driver_handle", text="Add/Edit driver", toggle=False)
        row = col_d.row(align=True)
        row.prop(propgrp, "add_driver_type", expand=True)
        if propgrp.add_driver_type == _ADD_DRIVER_TYPE_NEW_ARMATRUE:
            col_d.prop(propgrp, "new_name_for_driver_target", text="Name")
            col_d.prop(propgrp, "is_create_driver_parent_transmitter", text="Create transmitter")
        if propgrp.add_driver_type == _ADD_DRIVER_TYPE_SPECIFIC:
            col_d.prop_search(propgrp, "specific_add_driver_target", bpy.data, "objects", text="")
            try:

                if bpy.data.objects[propgrp.specific_add_driver_target].type != "ARMATURE":
                    col_d.label(text="Target is armature only.", icon="ERROR")

            except KeyError:

                pass

            col_d.prop(propgrp, "is_create_driver_parent_transmitter", text="Create transmitter")

        col.separator()

        col.label(text="Details:")
        box_dt = box.box()
        box_dt.label(text="prefix/suffix/identifier etc...")
        col_dt = box_dt.column()
        col_dt.prop(propgrp, "handle_identifier", text="handle")
        col_dt.prop(propgrp, "head_identifier", text="head")
        col_dt.prop(propgrp, "tail_identifier", text="tail")
        col_dt.prop(propgrp, "driver_handle_in_identifier", text="driver(in)")
        col_dt.prop(propgrp, "driver_handle_out_identifier", text="driver(out)")
        col_dt.prop(propgrp, "driver_parent_transmitter_identifier", text="transmitter")


class SetupBendyBoneAutoUIForPose(bpy.types.Panel):
    bl_label = "Setup Bendy Bone Auto"
    bl_idname = "UILER_SETUP_BENDY_BONE_AUTO_FOR_POSE_UI_PT_layout"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SBB"
    bl_context = "posemode"

    @classmethod
    def poll(cls, context):
        return "OK"

    def draw(self, context):

        layout = self.layout
        propgrp = bpy.context.window_manager.uil_setup_bendy_bone_auto_propgrp

        box = layout.box()
        box.label(text="Setup Bendy Bone:")
        row = box.row()
        col = row.column()
        col.operator("uiler.transformbendyboneforpose", text="Transform", icon="PLAY")
        col.prop(propgrp, "is_mirror", text="X-Axis mirror", toggle=False)
        col.prop(propgrp, "is_use_active_value", text="Use Active", toggle=False)

        box = layout.box()
        box.label(text="Rename bones:")
        col = box.column()
        col.operator("uiler.renameselectedbonesbyorderatbendybonesetupauto", text="Rename", icon="PLAY")
        col.prop(propgrp, "rename_bones_is_mirror", text="X-Axis mirror", toggle=False)
        col.prop(propgrp, "rename_bones_basename", text="base")
        col.prop(propgrp, "rename_bones_separator", text="separator")
        col.label(text="Incremental type:")
        col.row(align=True).prop(propgrp, "rename_bones_incremental_type", expand=True)
        if propgrp.rename_bones_incremental_type == _RENAME_BONES_INCREMENTAL_TYPE_ALPHA:
            col.row(align=True).prop(propgrp, "rename_bones_letters_case_type", expand=True)
        if propgrp.rename_bones_incremental_type == _RENAME_BONES_INCREMENTAL_TYPE_NUMBER:
            col.prop(propgrp, "rename_bones_padding_num", text="padding")
        if propgrp.rename_bones_incremental_type != _RENAME_BONES_INCREMENTAL_TYPE_NONE:
            col.prop(propgrp, "rename_bones_incremental_offset", text="offset")

        row2 = col.row()
        box = row2.box()
        col_m = box.column(align=True)
        row3 = col_m.row(align=True)
        row3.template_list("RENAMEBONESLIST_UL_items", "", propgrp, "rename_bones_grp", propgrp, "rename_bones_grp_idx", rows=3)

        col_r = row2.column(align=True)
        col_r.operator("uiler.addrenamebonesbyorderatbendybonesetupauto", text="", icon="ADD")
        col_r.operator("uiler.removerenamebonesbyorderatbendybonesetupauto", text="", icon="REMOVE")
        col_r.row(align=True).operator("uiler.refreshrenamebonesbyorderatbendybonesetupauto", text="", icon="FILE_REFRESH")
        col_r.separator()
        col_r.operator("uiler.uprenamebonesbyorderatbendybonesetupauto", icon='TRIA_UP', text="")
        col_r.operator("uiler.downrenamebonesbyorderatbendybonesetupauto", icon='TRIA_DOWN', text="")


class RENAMEBONESLIST_UL_items(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        row = layout.row()
        row.prop(item, "name", text="", icon="BONE_DATA", emboss=False, translate=False)

    def invoke(self, context, event):
        pass


classes = (
    RenameBoneNamePropGrp,
    RenameBoneItemsPropGrp,
    SetupBendyBoneProperties,
)

classes2 = (
    AddFunction,
    BendyBonePoseConfirmOperation,
    DownFunction,
    # DriverHandleBoneInfo,
    RefreshFunction,
    RemoveFunction,
    # RenameBoneInfo,
    RENAMEBONESLIST_UL_items,
    RenameBySelectedOrder,
    SetupBendyBoneAuto,
    SetupBendyBoneAutoUIForEdit,
    SetupBendyBoneAutoUIForPose,
    # TempParentHandle,
    TransformBendyBoneForPose,
    UpFunction,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    for cls in classes2:
        register_class(cls)

    _defProperties()


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)
    for cls in classes2:
        unregister_class(cls)


if __name__ == "__main__":
    register()
