// Generated by the protocol buffer compiler.  DO NOT EDIT!
// source: parameter.proto

#ifndef GOOGLE_PROTOBUF_INCLUDED_parameter_2eproto
#define GOOGLE_PROTOBUF_INCLUDED_parameter_2eproto

#include <limits>
#include <string>

#include <google/protobuf/port_def.inc>
#if PROTOBUF_VERSION < 3013000
#error This file was generated by a newer version of protoc which is
#error incompatible with your Protocol Buffer headers. Please update
#error your headers.
#endif
#if 3013000 < PROTOBUF_MIN_PROTOC_VERSION
#error This file was generated by an older version of protoc which is
#error incompatible with your Protocol Buffer headers. Please
#error regenerate this file with a newer version of protoc.
#endif

#include <google/protobuf/port_undef.inc>
#include <google/protobuf/io/coded_stream.h>
#include <google/protobuf/arena.h>
#include <google/protobuf/arenastring.h>
#include <google/protobuf/generated_message_table_driven.h>
#include <google/protobuf/generated_message_util.h>
#include <google/protobuf/inlined_string_field.h>
#include <google/protobuf/metadata_lite.h>
#include <google/protobuf/generated_message_reflection.h>
#include <google/protobuf/message.h>
#include <google/protobuf/repeated_field.h>  // IWYU pragma: export
#include <google/protobuf/extension_set.h>  // IWYU pragma: export
#include <google/protobuf/unknown_field_set.h>
// @@protoc_insertion_point(includes)
#include <google/protobuf/port_def.inc>
#define PROTOBUF_INTERNAL_EXPORT_parameter_2eproto
PROTOBUF_NAMESPACE_OPEN
namespace internal {
class AnyMetadata;
}  // namespace internal
PROTOBUF_NAMESPACE_CLOSE

// Internal implementation detail -- do not use these members.
struct TableStruct_parameter_2eproto {
  static const ::PROTOBUF_NAMESPACE_ID::internal::ParseTableField entries[]
    PROTOBUF_SECTION_VARIABLE(protodesc_cold);
  static const ::PROTOBUF_NAMESPACE_ID::internal::AuxiliaryParseTableField aux[]
    PROTOBUF_SECTION_VARIABLE(protodesc_cold);
  static const ::PROTOBUF_NAMESPACE_ID::internal::ParseTable schema[1]
    PROTOBUF_SECTION_VARIABLE(protodesc_cold);
  static const ::PROTOBUF_NAMESPACE_ID::internal::FieldMetadata field_metadata[];
  static const ::PROTOBUF_NAMESPACE_ID::internal::SerializationTable serialization_table[];
  static const ::PROTOBUF_NAMESPACE_ID::uint32 offsets[];
};
extern const ::PROTOBUF_NAMESPACE_ID::internal::DescriptorTable descriptor_table_parameter_2eproto;
namespace revolve {
namespace msgs {
class Parameter;
class ParameterDefaultTypeInternal;
extern ParameterDefaultTypeInternal _Parameter_default_instance_;
}  // namespace msgs
}  // namespace revolve
PROTOBUF_NAMESPACE_OPEN
template<> ::revolve::msgs::Parameter* Arena::CreateMaybeMessage<::revolve::msgs::Parameter>(Arena*);
PROTOBUF_NAMESPACE_CLOSE
namespace revolve {
namespace msgs {

// ===================================================================

class Parameter PROTOBUF_FINAL :
    public ::PROTOBUF_NAMESPACE_ID::Message /* @@protoc_insertion_point(class_definition:revolve.msgs.Parameter) */ {
 public:
  inline Parameter() : Parameter(nullptr) {}
  virtual ~Parameter();

  Parameter(const Parameter& from);
  Parameter(Parameter&& from) noexcept
    : Parameter() {
    *this = ::std::move(from);
  }

  inline Parameter& operator=(const Parameter& from) {
    CopyFrom(from);
    return *this;
  }
  inline Parameter& operator=(Parameter&& from) noexcept {
    if (GetArena() == from.GetArena()) {
      if (this != &from) InternalSwap(&from);
    } else {
      CopyFrom(from);
    }
    return *this;
  }

  inline const ::PROTOBUF_NAMESPACE_ID::UnknownFieldSet& unknown_fields() const {
    return _internal_metadata_.unknown_fields<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>(::PROTOBUF_NAMESPACE_ID::UnknownFieldSet::default_instance);
  }
  inline ::PROTOBUF_NAMESPACE_ID::UnknownFieldSet* mutable_unknown_fields() {
    return _internal_metadata_.mutable_unknown_fields<::PROTOBUF_NAMESPACE_ID::UnknownFieldSet>();
  }

  static const ::PROTOBUF_NAMESPACE_ID::Descriptor* descriptor() {
    return GetDescriptor();
  }
  static const ::PROTOBUF_NAMESPACE_ID::Descriptor* GetDescriptor() {
    return GetMetadataStatic().descriptor;
  }
  static const ::PROTOBUF_NAMESPACE_ID::Reflection* GetReflection() {
    return GetMetadataStatic().reflection;
  }
  static const Parameter& default_instance();

  static void InitAsDefaultInstance();  // FOR INTERNAL USE ONLY
  static inline const Parameter* internal_default_instance() {
    return reinterpret_cast<const Parameter*>(
               &_Parameter_default_instance_);
  }
  static constexpr int kIndexInFileMessages =
    0;

  friend void swap(Parameter& a, Parameter& b) {
    a.Swap(&b);
  }
  inline void Swap(Parameter* other) {
    if (other == this) return;
    if (GetArena() == other->GetArena()) {
      InternalSwap(other);
    } else {
      ::PROTOBUF_NAMESPACE_ID::internal::GenericSwap(this, other);
    }
  }
  void UnsafeArenaSwap(Parameter* other) {
    if (other == this) return;
    GOOGLE_DCHECK(GetArena() == other->GetArena());
    InternalSwap(other);
  }

  // implements Message ----------------------------------------------

  inline Parameter* New() const final {
    return CreateMaybeMessage<Parameter>(nullptr);
  }

  Parameter* New(::PROTOBUF_NAMESPACE_ID::Arena* arena) const final {
    return CreateMaybeMessage<Parameter>(arena);
  }
  void CopyFrom(const ::PROTOBUF_NAMESPACE_ID::Message& from) final;
  void MergeFrom(const ::PROTOBUF_NAMESPACE_ID::Message& from) final;
  void CopyFrom(const Parameter& from);
  void MergeFrom(const Parameter& from);
  PROTOBUF_ATTRIBUTE_REINITIALIZES void Clear() final;
  bool IsInitialized() const final;

  size_t ByteSizeLong() const final;
  const char* _InternalParse(const char* ptr, ::PROTOBUF_NAMESPACE_ID::internal::ParseContext* ctx) final;
  ::PROTOBUF_NAMESPACE_ID::uint8* _InternalSerialize(
      ::PROTOBUF_NAMESPACE_ID::uint8* target, ::PROTOBUF_NAMESPACE_ID::io::EpsCopyOutputStream* stream) const final;
  int GetCachedSize() const final { return _cached_size_.Get(); }

  private:
  inline void SharedCtor();
  inline void SharedDtor();
  void SetCachedSize(int size) const final;
  void InternalSwap(Parameter* other);
  friend class ::PROTOBUF_NAMESPACE_ID::internal::AnyMetadata;
  static ::PROTOBUF_NAMESPACE_ID::StringPiece FullMessageName() {
    return "revolve.msgs.Parameter";
  }
  protected:
  explicit Parameter(::PROTOBUF_NAMESPACE_ID::Arena* arena);
  private:
  static void ArenaDtor(void* object);
  inline void RegisterArenaDtor(::PROTOBUF_NAMESPACE_ID::Arena* arena);
  public:

  ::PROTOBUF_NAMESPACE_ID::Metadata GetMetadata() const final;
  private:
  static ::PROTOBUF_NAMESPACE_ID::Metadata GetMetadataStatic() {
    ::PROTOBUF_NAMESPACE_ID::internal::AssignDescriptors(&::descriptor_table_parameter_2eproto);
    return ::descriptor_table_parameter_2eproto.file_level_metadata[kIndexInFileMessages];
  }

  public:

  // nested types ----------------------------------------------------

  // accessors -------------------------------------------------------

  enum : int {
    kValueFieldNumber = 1,
  };
  // required double value = 1;
  bool has_value() const;
  private:
  bool _internal_has_value() const;
  public:
  void clear_value();
  double value() const;
  void set_value(double value);
  private:
  double _internal_value() const;
  void _internal_set_value(double value);
  public:

  // @@protoc_insertion_point(class_scope:revolve.msgs.Parameter)
 private:
  class _Internal;

  template <typename T> friend class ::PROTOBUF_NAMESPACE_ID::Arena::InternalHelper;
  typedef void InternalArenaConstructable_;
  typedef void DestructorSkippable_;
  ::PROTOBUF_NAMESPACE_ID::internal::HasBits<1> _has_bits_;
  mutable ::PROTOBUF_NAMESPACE_ID::internal::CachedSize _cached_size_;
  double value_;
  friend struct ::TableStruct_parameter_2eproto;
};
// ===================================================================


// ===================================================================

#ifdef __GNUC__
  #pragma GCC diagnostic push
  #pragma GCC diagnostic ignored "-Wstrict-aliasing"
#endif  // __GNUC__
// Parameter

// required double value = 1;
inline bool Parameter::_internal_has_value() const {
  bool value = (_has_bits_[0] & 0x00000001u) != 0;
  return value;
}
inline bool Parameter::has_value() const {
  return _internal_has_value();
}
inline void Parameter::clear_value() {
  value_ = 0;
  _has_bits_[0] &= ~0x00000001u;
}
inline double Parameter::_internal_value() const {
  return value_;
}
inline double Parameter::value() const {
  // @@protoc_insertion_point(field_get:revolve.msgs.Parameter.value)
  return _internal_value();
}
inline void Parameter::_internal_set_value(double value) {
  _has_bits_[0] |= 0x00000001u;
  value_ = value;
}
inline void Parameter::set_value(double value) {
  _internal_set_value(value);
  // @@protoc_insertion_point(field_set:revolve.msgs.Parameter.value)
}

#ifdef __GNUC__
  #pragma GCC diagnostic pop
#endif  // __GNUC__

// @@protoc_insertion_point(namespace_scope)

}  // namespace msgs
}  // namespace revolve

// @@protoc_insertion_point(global_scope)

#include <google/protobuf/port_undef.inc>
#endif  // GOOGLE_PROTOBUF_INCLUDED_GOOGLE_PROTOBUF_INCLUDED_parameter_2eproto
