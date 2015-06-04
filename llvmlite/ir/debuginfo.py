from __future__ import absolute_import, print_function, division

from enum import IntEnum
from os.path import dirname

import llvmlite
from .types import IntType
from .values import MetaDataString, MDValue, Constant, MetaDataNull

llvm_debug_version = 0xc0000


class DI_Tag(IntEnum):
    DW_TAG_compile_unit = 17
    DW_TAG_subprogram = 46
    DW_TAG_file_type = 41
    DW_TAG_subroutine_type = 21
    DW_TAG_base_type = 36
    DW_TAG_array_type = 1
    DW_TAG_enumeration_type = 4
    DW_TAG_structure_type = 19
    DW_TAG_union_type = 23
    DW_TAG_inheritance = 28


class DI_Attribute(IntEnum):
    DW_AT_sibling = 0x01
    DW_AT_location = 0x02
    DW_AT_name = 0x03
    DW_AT_ordering = 0x09
    DW_AT_byte_size = 0x0b
    DW_AT_bit_offset = 0x0c
    DW_AT_bit_size = 0x0d
    DW_AT_stmt_list = 0x10
    DW_AT_low_pc = 0x11
    DW_AT_high_pc = 0x12
    DW_AT_language = 0x13
    DW_AT_discr = 0x15
    DW_AT_discr_value = 0x16
    DW_AT_visibility = 0x17
    DW_AT_import = 0x18
    DW_AT_string_length = 0x19
    DW_AT_common_reference = 0x1a
    DW_AT_comp_dir = 0x1b
    DW_AT_const_value = 0x1c
    DW_AT_containing_type = 0x1d
    DW_AT_default_value = 0x1e
    DW_AT_inline = 0x20
    DW_AT_is_optional = 0x21
    DW_AT_lower_bound = 0x22
    DW_AT_producer = 0x25
    DW_AT_prototyped = 0x27
    DW_AT_return_addr = 0x2a
    DW_AT_start_scope = 0x2c
    DW_AT_bit_stride = 0x2e
    DW_AT_upper_bound = 0x2f
    DW_AT_abstract_origin = 0x31
    DW_AT_accessibility = 0x32
    DW_AT_address_class = 0x33
    DW_AT_artificial = 0x34
    DW_AT_base_types = 0x35
    DW_AT_calling_convention = 0x36
    DW_AT_count = 0x37
    DW_AT_data_member_location = 0x38
    DW_AT_decl_column = 0x39
    DW_AT_decl_file = 0x3a
    DW_AT_decl_line = 0x3b
    DW_AT_declaration = 0x3c
    DW_AT_discr_list = 0x3d
    DW_AT_encoding = 0x3e
    DW_AT_external = 0x3f
    DW_AT_frame_base = 0x40
    DW_AT_friend = 0x41
    DW_AT_identifier_case = 0x42
    DW_AT_macro_info = 0x43
    DW_AT_namelist_item = 0x44
    DW_AT_priority = 0x45
    DW_AT_segment = 0x46
    DW_AT_specification = 0x47
    DW_AT_static_link = 0x48
    DW_AT_type = 0x49
    DW_AT_use_location = 0x4a
    DW_AT_variable_parameter = 0x4b
    DW_AT_virtuality = 0x4c
    DW_AT_vtable_elem_location = 0x4d
    DW_AT_allocated = 0x4e
    DW_AT_associated = 0x4f
    DW_AT_data_location = 0x50
    DW_AT_byte_stride = 0x51
    DW_AT_entry_pc = 0x52
    DW_AT_use_UTF8 = 0x53
    DW_AT_extension = 0x54
    DW_AT_ranges = 0x55
    DW_AT_trampoline = 0x56
    DW_AT_call_column = 0x57
    DW_AT_call_file = 0x58
    DW_AT_call_line = 0x59
    DW_AT_description = 0x5a
    DW_AT_binary_scale = 0x5b
    DW_AT_decimal_scale = 0x5c
    DW_AT_small = 0x5d
    DW_AT_decimal_sign = 0x5e
    DW_AT_digit_count = 0x5f
    DW_AT_picture_string = 0x60
    DW_AT_mutable = 0x61
    DW_AT_threads_scaled = 0x62
    DW_AT_explicit = 0x63
    DW_AT_object_pointer = 0x64
    DW_AT_endianity = 0x65
    DW_AT_elemental = 0x66
    DW_AT_pure = 0x67
    DW_AT_recursive = 0x68
    DW_AT_signature = 0x69
    DW_AT_main_subprogram = 0x6a
    DW_AT_data_bit_offset = 0x6b
    DW_AT_const_expr = 0x6c
    DW_AT_enum_class = 0x6d
    DW_AT_linkage_name = 0x6e

    # New in DWARF 5
    DW_AT_string_length_bit_size = 0x6f
    DW_AT_string_length_byte_size = 0x70
    DW_AT_rank = 0x71
    DW_AT_str_offsets_base = 0x72
    DW_AT_addr_base = 0x73
    DW_AT_ranges_base = 0x74
    DW_AT_dwo_id = 0x75
    DW_AT_dwo_name = 0x76
    DW_AT_reference = 0x77
    DW_AT_rvalue_reference = 0x78

    DW_AT_lo_user = 0x2000
    DW_AT_hi_user = 0x3fff


class DI_TypeKind(IntEnum):
    DW_ATE_address = 0x01
    DW_ATE_boolean = 0x02
    DW_ATE_complex_float = 0x03
    DW_ATE_float = 0x04
    DW_ATE_signed = 0x05
    DW_ATE_signed_char = 0x06
    DW_ATE_unsigned = 0x07
    DW_ATE_unsigned_char = 0x08
    DW_ATE_imaginary_float = 0x09
    DW_ATE_packed_decimal = 0x0a
    DW_ATE_numeric_string = 0x0b
    DW_ATE_edited = 0x0c
    DW_ATE_signed_fixed = 0x0d
    DW_ATE_unsigned_fixed = 0x0e
    DW_ATE_decimal_float = 0x0f
    DW_ATE_UTF = 0x10
    DW_ATE_lo_user = 0x80
    DW_ATE_hi_user = 0xff


I32 = IntType(32)
I64 = IntType(64)
I1 = IntType(1)


class DIBuilder(object):
    def __init__(self, module, filepath, optimized=False, runtime_version=0):
        self.module = module
        self.optimized = optimized
        self.runtime_version = runtime_version
        self.file_directory_pair = self.create_file_directory_pair(filepath)
        self.subprograms = self._md_node()
        self.global_variables = self._md_node()
        self.context_descriptor = self.create_context_descriptor(
            self.file_directory_pair)

        # init
        dwarf_version = self._md_node(
            Constant(I32, 2),
            self._md_string("Dwarf Version"),
            Constant(I32, 4),
        )
        di_version = self._md_node(
            Constant(I32, 2),
            self._md_string("Debug Info Version"),
            Constant(I32, 1),
        )
        self.module_flags = module.add_named_metadata('llvm.module.flags')
        self.module_flags.add(dwarf_version)
        self.module_flags.add(di_version)
        self.dbg_cu = module.add_named_metadata('llvm.dbg.cu')
        self.ident = module.add_named_metadata("llvm.ident")
        self.ident.add(self._md_node(self._md_string("llvmlite")))

    def create_compile_unit(self):
        tag = llvm_debug_version + DI_Tag.DW_TAG_compile_unit
        lang = 4  # XXX: C++
        flags = self._md_string("")
        # XXX not supported
        enum_types = retained_types = imported_entities = self._md_node()
        split_debug_filename = self._md_string("")
        vals = [
            Constant(I32, tag),
            self.file_directory_pair,
            Constant(I32, lang),
            self._md_string("llvmlite {0}".format(llvmlite.__version__)),
            Constant(I1, self.optimized),
            flags,
            Constant(I32, self.runtime_version),
            enum_types,
            retained_types,
            self.subprograms,
            self.global_variables,
            imported_entities,
            split_debug_filename,
            # Constant(I32, 1), # clang would generate this
        ]
        cu = self._md_node(*vals)
        self.dbg_cu.add(cu)
        return cu

    def add_subprogram(self, func, name, return_type=None, argument_types=(),
                       lineno=0, lineno_scope=0, is_local=False,
                       is_defined=True, is_optimized=False):
        tag = llvm_debug_version + DI_Tag.DW_TAG_subprogram
        fn_name = display_name = self._md_string(name)
        mip_linkage_name_cpp = self._md_string("")
        virtuality = 0
        virtual_index = 0
        flags = 0  # clang would use 256
        func_var_list = self._md_node()
        func_decl_desc = template_params = vtable_base_type = self._md_null()
        typ = self.create_subroutine_type(return_type, argument_types)
        vals = [
            Constant(I32, tag),
            self.file_directory_pair,
            self.context_descriptor,
            fn_name,
            display_name,
            mip_linkage_name_cpp,
            Constant(I32, lineno),
            typ,
            Constant(I1, int(is_local)),
            Constant(I1, int(is_defined)),
            Constant(I32, virtuality),
            Constant(I32, virtual_index),
            vtable_base_type,
            Constant(I32, flags),
            Constant(I1, is_optimized),
            func,
            template_params,
            func_decl_desc,
            func_var_list,
            Constant(I32, lineno_scope),
        ]
        md = self._md_node(*vals)
        self.subprograms.append(md)
        return md

    def create_base_type(self, typename, kind, size, align=None, offset=0,
                         filepath=None, lineno=0):
        """
        Args
        ----
        typename: str
            Name of type. Maybe "" for anonymous types.
        kind: int
            DI_TypeKind
        size: int
        align: int or None
        offset: int
        filepath: str
            Path to file where type is defined.
        lineno: int

        """
        if filepath is None:
            file_dir_pair = self._md_null()
        else:
            file_dir_pair = self.create_file_directory_pair(filepath)

        tag = llvm_debug_version + DI_Tag.DW_TAG_base_type
        flags = 0
        vals = [
            Constant(I32, tag),
            file_dir_pair,
            self._md_null(),
            self._md_string(typename),
            Constant(I32, lineno),
            Constant(I64, size),
            Constant(I64, align if align is not None else size),
            Constant(I64, offset),
            Constant(I32, flags),
            Constant(I32, kind.value),
        ]
        return self._md_node(*vals)

    def create_subroutine_type(self, return_type, argument_types, typename='',
                               filepath=None, lineno=0):
        tag = DI_Tag.DW_TAG_subroutine_type
        if return_type is None:
            return_type = self._md_null()
        members = [return_type] + list(argument_types)
        return self.create_composite_type(tag,
                                          members,
                                          size=0,
                                          typename=typename,
                                          filepath=filepath,
                                          lineno=lineno)

    def create_composite_type(self, tag, members, size, align=None, offset=0,
                              typename='', filepath=None, lineno=0):
        if filepath is None:
            file_dir_pair = self._md_null()
        else:
            file_dir_pair = self.create_file_directory_pair(filepath)

        tag = llvm_debug_version + tag
        align = size if align is None else align
        flags = 0
        runtime_lang = 0
        derived = vtable = template_params = purpose = self._md_null()
        members = self._md_node(*members)
        vals = [
            Constant(I32, tag),
            Constant(I32, 0),
            file_dir_pair,
            self._md_string(typename),
            Constant(I32, lineno),
            Constant(I64, size),
            Constant(I64, align),
            Constant(I64, offset),
            Constant(I32, flags),
            derived,
            members,
            Constant(I32, runtime_lang),
            vtable,
            template_params,
            purpose,
        ]
        return self._md_node(*vals)

    def create_file_directory_pair(self, filepath):
        dname = dirname(filepath)
        fname = filepath[len(dname):]
        return self._md_node(self._md_string(fname),
                             self._md_string(dname))

    def create_context_descriptor(self, md_file_dir_pair):
        tag = llvm_debug_version + DI_Tag.DW_TAG_file_type
        return self._md_node(Constant(I32, tag), md_file_dir_pair)

    def _md_string(self, text):
        return MetaDataString(self.module, text)

    def _md_node(self, *values):
        return MDValue(self.module, values, name='')

    def _md_null(self):
        return MetaDataNull()
