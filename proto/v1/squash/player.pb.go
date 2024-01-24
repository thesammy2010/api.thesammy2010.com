// Code generated by protoc-gen-go. DO NOT EDIT.
// versions:
// 	protoc-gen-go v1.32.0
// 	protoc        (unknown)
// source: proto/v1/squash/player.proto

package proto

import (
	_ "google.golang.org/genproto/googleapis/api/annotations"
	protoreflect "google.golang.org/protobuf/reflect/protoreflect"
	protoimpl "google.golang.org/protobuf/runtime/protoimpl"
	timestamppb "google.golang.org/protobuf/types/known/timestamppb"
	wrapperspb "google.golang.org/protobuf/types/known/wrapperspb"
	reflect "reflect"
	sync "sync"
)

const (
	// Verify that this generated code is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(20 - protoimpl.MinVersion)
	// Verify that runtime/protoimpl is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(protoimpl.MaxVersion - 20)
)

type SquashPlayer struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	// @inject_tag: `bun:"column_name:id,type:uuid,pk,default:gen_random_uuid()"`
	Id string `protobuf:"bytes,1,opt,name=id,proto3" json:"id,omitempty" bun:"column_name:id,type:uuid,pk,default:gen_random_uuid()"`
	// @inject_tag: `bun:",nullzero"`
	Name string `protobuf:"bytes,2,opt,name=name,proto3" json:"name,omitempty" bun:",nullzero"`
	// @inject_tag: `bun:"default:null,nullzero"`
	EmailAddress string `protobuf:"bytes,3,opt,name=email_address,json=emailAddress,proto3" json:"email_address,omitempty" bun:"default:null,nullzero"`
	// @inject_tag: `bun:"default:null,nullzero"`
	ProfilePicture []byte `protobuf:"bytes,4,opt,name=profile_picture,json=profilePicture,proto3" json:"profile_picture,omitempty" bun:"default:null,nullzero"`
	// @inject_tag: bun:”type:timestamptz,default:now()”
	CreatedAt *timestamppb.Timestamp `protobuf:"bytes,5,opt,name=created_at,json=createdAt,proto3" json:"created_at,omitempty"`
	// @inject_tag: bun:”type:timestamptz,default:now()”
	UpdatedAt *timestamppb.Timestamp `protobuf:"bytes,6,opt,name=updated_at,json=updatedAt,proto3" json:"updated_at,omitempty"`
}

func (x *SquashPlayer) Reset() {
	*x = SquashPlayer{}
	if protoimpl.UnsafeEnabled {
		mi := &file_proto_v1_squash_player_proto_msgTypes[0]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *SquashPlayer) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*SquashPlayer) ProtoMessage() {}

func (x *SquashPlayer) ProtoReflect() protoreflect.Message {
	mi := &file_proto_v1_squash_player_proto_msgTypes[0]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use SquashPlayer.ProtoReflect.Descriptor instead.
func (*SquashPlayer) Descriptor() ([]byte, []int) {
	return file_proto_v1_squash_player_proto_rawDescGZIP(), []int{0}
}

func (x *SquashPlayer) GetId() string {
	if x != nil {
		return x.Id
	}
	return ""
}

func (x *SquashPlayer) GetName() string {
	if x != nil {
		return x.Name
	}
	return ""
}

func (x *SquashPlayer) GetEmailAddress() string {
	if x != nil {
		return x.EmailAddress
	}
	return ""
}

func (x *SquashPlayer) GetProfilePicture() []byte {
	if x != nil {
		return x.ProfilePicture
	}
	return nil
}

func (x *SquashPlayer) GetCreatedAt() *timestamppb.Timestamp {
	if x != nil {
		return x.CreatedAt
	}
	return nil
}

func (x *SquashPlayer) GetUpdatedAt() *timestamppb.Timestamp {
	if x != nil {
		return x.UpdatedAt
	}
	return nil
}

// CREATE
type CreateSquashPlayerRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Name           string `protobuf:"bytes,1,opt,name=name,proto3" json:"name,omitempty"`
	EmailAddress   string `protobuf:"bytes,2,opt,name=email_address,json=emailAddress,proto3" json:"email_address,omitempty"`
	ProfilePicture []byte `protobuf:"bytes,3,opt,name=profile_picture,json=profilePicture,proto3" json:"profile_picture,omitempty"`
}

func (x *CreateSquashPlayerRequest) Reset() {
	*x = CreateSquashPlayerRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_proto_v1_squash_player_proto_msgTypes[1]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *CreateSquashPlayerRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*CreateSquashPlayerRequest) ProtoMessage() {}

func (x *CreateSquashPlayerRequest) ProtoReflect() protoreflect.Message {
	mi := &file_proto_v1_squash_player_proto_msgTypes[1]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use CreateSquashPlayerRequest.ProtoReflect.Descriptor instead.
func (*CreateSquashPlayerRequest) Descriptor() ([]byte, []int) {
	return file_proto_v1_squash_player_proto_rawDescGZIP(), []int{1}
}

func (x *CreateSquashPlayerRequest) GetName() string {
	if x != nil {
		return x.Name
	}
	return ""
}

func (x *CreateSquashPlayerRequest) GetEmailAddress() string {
	if x != nil {
		return x.EmailAddress
	}
	return ""
}

func (x *CreateSquashPlayerRequest) GetProfilePicture() []byte {
	if x != nil {
		return x.ProfilePicture
	}
	return nil
}

type CreateSquashPlayerResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Id string `protobuf:"bytes,1,opt,name=id,proto3" json:"id,omitempty"`
}

func (x *CreateSquashPlayerResponse) Reset() {
	*x = CreateSquashPlayerResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_proto_v1_squash_player_proto_msgTypes[2]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *CreateSquashPlayerResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*CreateSquashPlayerResponse) ProtoMessage() {}

func (x *CreateSquashPlayerResponse) ProtoReflect() protoreflect.Message {
	mi := &file_proto_v1_squash_player_proto_msgTypes[2]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use CreateSquashPlayerResponse.ProtoReflect.Descriptor instead.
func (*CreateSquashPlayerResponse) Descriptor() ([]byte, []int) {
	return file_proto_v1_squash_player_proto_rawDescGZIP(), []int{2}
}

func (x *CreateSquashPlayerResponse) GetId() string {
	if x != nil {
		return x.Id
	}
	return ""
}

// READ 1
type GetSquashPlayerRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Id string `protobuf:"bytes,1,opt,name=id,proto3" json:"id,omitempty"`
}

func (x *GetSquashPlayerRequest) Reset() {
	*x = GetSquashPlayerRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_proto_v1_squash_player_proto_msgTypes[3]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *GetSquashPlayerRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*GetSquashPlayerRequest) ProtoMessage() {}

func (x *GetSquashPlayerRequest) ProtoReflect() protoreflect.Message {
	mi := &file_proto_v1_squash_player_proto_msgTypes[3]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use GetSquashPlayerRequest.ProtoReflect.Descriptor instead.
func (*GetSquashPlayerRequest) Descriptor() ([]byte, []int) {
	return file_proto_v1_squash_player_proto_rawDescGZIP(), []int{3}
}

func (x *GetSquashPlayerRequest) GetId() string {
	if x != nil {
		return x.Id
	}
	return ""
}

type GetSquashPlayerResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	SquashPlayer *SquashPlayer `protobuf:"bytes,2,opt,name=squash_player,json=squashPlayer,proto3" json:"squash_player,omitempty"`
}

func (x *GetSquashPlayerResponse) Reset() {
	*x = GetSquashPlayerResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_proto_v1_squash_player_proto_msgTypes[4]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *GetSquashPlayerResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*GetSquashPlayerResponse) ProtoMessage() {}

func (x *GetSquashPlayerResponse) ProtoReflect() protoreflect.Message {
	mi := &file_proto_v1_squash_player_proto_msgTypes[4]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use GetSquashPlayerResponse.ProtoReflect.Descriptor instead.
func (*GetSquashPlayerResponse) Descriptor() ([]byte, []int) {
	return file_proto_v1_squash_player_proto_rawDescGZIP(), []int{4}
}

func (x *GetSquashPlayerResponse) GetSquashPlayer() *SquashPlayer {
	if x != nil {
		return x.SquashPlayer
	}
	return nil
}

// READ ALL
type GetAllSquashPlayersRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields
}

func (x *GetAllSquashPlayersRequest) Reset() {
	*x = GetAllSquashPlayersRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_proto_v1_squash_player_proto_msgTypes[5]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *GetAllSquashPlayersRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*GetAllSquashPlayersRequest) ProtoMessage() {}

func (x *GetAllSquashPlayersRequest) ProtoReflect() protoreflect.Message {
	mi := &file_proto_v1_squash_player_proto_msgTypes[5]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use GetAllSquashPlayersRequest.ProtoReflect.Descriptor instead.
func (*GetAllSquashPlayersRequest) Descriptor() ([]byte, []int) {
	return file_proto_v1_squash_player_proto_rawDescGZIP(), []int{5}
}

type GetAllSquashPlayersResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	SquashPlayers []*SquashPlayer `protobuf:"bytes,1,rep,name=squash_players,json=squashPlayers,proto3" json:"squash_players,omitempty"`
}

func (x *GetAllSquashPlayersResponse) Reset() {
	*x = GetAllSquashPlayersResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_proto_v1_squash_player_proto_msgTypes[6]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *GetAllSquashPlayersResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*GetAllSquashPlayersResponse) ProtoMessage() {}

func (x *GetAllSquashPlayersResponse) ProtoReflect() protoreflect.Message {
	mi := &file_proto_v1_squash_player_proto_msgTypes[6]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use GetAllSquashPlayersResponse.ProtoReflect.Descriptor instead.
func (*GetAllSquashPlayersResponse) Descriptor() ([]byte, []int) {
	return file_proto_v1_squash_player_proto_rawDescGZIP(), []int{6}
}

func (x *GetAllSquashPlayersResponse) GetSquashPlayers() []*SquashPlayer {
	if x != nil {
		return x.SquashPlayers
	}
	return nil
}

// UPDATE
type UpdateSquashPlayerRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Id             string                  `protobuf:"bytes,1,opt,name=id,proto3" json:"id,omitempty"`
	Name           *wrapperspb.StringValue `protobuf:"bytes,2,opt,name=name,proto3" json:"name,omitempty"`
	EmailAddress   *wrapperspb.StringValue `protobuf:"bytes,3,opt,name=email_address,json=emailAddress,proto3" json:"email_address,omitempty"`
	ProfilePicture *wrapperspb.BytesValue  `protobuf:"bytes,4,opt,name=profile_picture,json=profilePicture,proto3" json:"profile_picture,omitempty"`
}

func (x *UpdateSquashPlayerRequest) Reset() {
	*x = UpdateSquashPlayerRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_proto_v1_squash_player_proto_msgTypes[7]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *UpdateSquashPlayerRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*UpdateSquashPlayerRequest) ProtoMessage() {}

func (x *UpdateSquashPlayerRequest) ProtoReflect() protoreflect.Message {
	mi := &file_proto_v1_squash_player_proto_msgTypes[7]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use UpdateSquashPlayerRequest.ProtoReflect.Descriptor instead.
func (*UpdateSquashPlayerRequest) Descriptor() ([]byte, []int) {
	return file_proto_v1_squash_player_proto_rawDescGZIP(), []int{7}
}

func (x *UpdateSquashPlayerRequest) GetId() string {
	if x != nil {
		return x.Id
	}
	return ""
}

func (x *UpdateSquashPlayerRequest) GetName() *wrapperspb.StringValue {
	if x != nil {
		return x.Name
	}
	return nil
}

func (x *UpdateSquashPlayerRequest) GetEmailAddress() *wrapperspb.StringValue {
	if x != nil {
		return x.EmailAddress
	}
	return nil
}

func (x *UpdateSquashPlayerRequest) GetProfilePicture() *wrapperspb.BytesValue {
	if x != nil {
		return x.ProfilePicture
	}
	return nil
}

type UpdateSquashPlayerResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	SquashPlayer *SquashPlayer `protobuf:"bytes,1,opt,name=squash_player,json=squashPlayer,proto3" json:"squash_player,omitempty"`
}

func (x *UpdateSquashPlayerResponse) Reset() {
	*x = UpdateSquashPlayerResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_proto_v1_squash_player_proto_msgTypes[8]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *UpdateSquashPlayerResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*UpdateSquashPlayerResponse) ProtoMessage() {}

func (x *UpdateSquashPlayerResponse) ProtoReflect() protoreflect.Message {
	mi := &file_proto_v1_squash_player_proto_msgTypes[8]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use UpdateSquashPlayerResponse.ProtoReflect.Descriptor instead.
func (*UpdateSquashPlayerResponse) Descriptor() ([]byte, []int) {
	return file_proto_v1_squash_player_proto_rawDescGZIP(), []int{8}
}

func (x *UpdateSquashPlayerResponse) GetSquashPlayer() *SquashPlayer {
	if x != nil {
		return x.SquashPlayer
	}
	return nil
}

// DELETE
type DeleteSquashPlayerRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Id string `protobuf:"bytes,2,opt,name=id,proto3" json:"id,omitempty"`
}

func (x *DeleteSquashPlayerRequest) Reset() {
	*x = DeleteSquashPlayerRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_proto_v1_squash_player_proto_msgTypes[9]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *DeleteSquashPlayerRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*DeleteSquashPlayerRequest) ProtoMessage() {}

func (x *DeleteSquashPlayerRequest) ProtoReflect() protoreflect.Message {
	mi := &file_proto_v1_squash_player_proto_msgTypes[9]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use DeleteSquashPlayerRequest.ProtoReflect.Descriptor instead.
func (*DeleteSquashPlayerRequest) Descriptor() ([]byte, []int) {
	return file_proto_v1_squash_player_proto_rawDescGZIP(), []int{9}
}

func (x *DeleteSquashPlayerRequest) GetId() string {
	if x != nil {
		return x.Id
	}
	return ""
}

type DeleteSquashPlayerResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Id string `protobuf:"bytes,3,opt,name=id,proto3" json:"id,omitempty"`
}

func (x *DeleteSquashPlayerResponse) Reset() {
	*x = DeleteSquashPlayerResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_proto_v1_squash_player_proto_msgTypes[10]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *DeleteSquashPlayerResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*DeleteSquashPlayerResponse) ProtoMessage() {}

func (x *DeleteSquashPlayerResponse) ProtoReflect() protoreflect.Message {
	mi := &file_proto_v1_squash_player_proto_msgTypes[10]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use DeleteSquashPlayerResponse.ProtoReflect.Descriptor instead.
func (*DeleteSquashPlayerResponse) Descriptor() ([]byte, []int) {
	return file_proto_v1_squash_player_proto_rawDescGZIP(), []int{10}
}

func (x *DeleteSquashPlayerResponse) GetId() string {
	if x != nil {
		return x.Id
	}
	return ""
}

var File_proto_v1_squash_player_proto protoreflect.FileDescriptor

var file_proto_v1_squash_player_proto_rawDesc = []byte{
	0x0a, 0x1c, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x2f, 0x76, 0x31, 0x2f, 0x73, 0x71, 0x75, 0x61, 0x73,
	0x68, 0x2f, 0x70, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x1a, 0x1c,
	0x67, 0x6f, 0x6f, 0x67, 0x6c, 0x65, 0x2f, 0x61, 0x70, 0x69, 0x2f, 0x61, 0x6e, 0x6e, 0x6f, 0x74,
	0x61, 0x74, 0x69, 0x6f, 0x6e, 0x73, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x1a, 0x1e, 0x67, 0x6f,
	0x6f, 0x67, 0x6c, 0x65, 0x2f, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2f, 0x77, 0x72,
	0x61, 0x70, 0x70, 0x65, 0x72, 0x73, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x1a, 0x1f, 0x67, 0x6f,
	0x6f, 0x67, 0x6c, 0x65, 0x2f, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2f, 0x74, 0x69,
	0x6d, 0x65, 0x73, 0x74, 0x61, 0x6d, 0x70, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x22, 0xf6, 0x01,
	0x0a, 0x0c, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x12, 0x0e,
	0x0a, 0x02, 0x69, 0x64, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x02, 0x69, 0x64, 0x12, 0x12,
	0x0a, 0x04, 0x6e, 0x61, 0x6d, 0x65, 0x18, 0x02, 0x20, 0x01, 0x28, 0x09, 0x52, 0x04, 0x6e, 0x61,
	0x6d, 0x65, 0x12, 0x23, 0x0a, 0x0d, 0x65, 0x6d, 0x61, 0x69, 0x6c, 0x5f, 0x61, 0x64, 0x64, 0x72,
	0x65, 0x73, 0x73, 0x18, 0x03, 0x20, 0x01, 0x28, 0x09, 0x52, 0x0c, 0x65, 0x6d, 0x61, 0x69, 0x6c,
	0x41, 0x64, 0x64, 0x72, 0x65, 0x73, 0x73, 0x12, 0x27, 0x0a, 0x0f, 0x70, 0x72, 0x6f, 0x66, 0x69,
	0x6c, 0x65, 0x5f, 0x70, 0x69, 0x63, 0x74, 0x75, 0x72, 0x65, 0x18, 0x04, 0x20, 0x01, 0x28, 0x0c,
	0x52, 0x0e, 0x70, 0x72, 0x6f, 0x66, 0x69, 0x6c, 0x65, 0x50, 0x69, 0x63, 0x74, 0x75, 0x72, 0x65,
	0x12, 0x39, 0x0a, 0x0a, 0x63, 0x72, 0x65, 0x61, 0x74, 0x65, 0x64, 0x5f, 0x61, 0x74, 0x18, 0x05,
	0x20, 0x01, 0x28, 0x0b, 0x32, 0x1a, 0x2e, 0x67, 0x6f, 0x6f, 0x67, 0x6c, 0x65, 0x2e, 0x70, 0x72,
	0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2e, 0x54, 0x69, 0x6d, 0x65, 0x73, 0x74, 0x61, 0x6d, 0x70,
	0x52, 0x09, 0x63, 0x72, 0x65, 0x61, 0x74, 0x65, 0x64, 0x41, 0x74, 0x12, 0x39, 0x0a, 0x0a, 0x75,
	0x70, 0x64, 0x61, 0x74, 0x65, 0x64, 0x5f, 0x61, 0x74, 0x18, 0x06, 0x20, 0x01, 0x28, 0x0b, 0x32,
	0x1a, 0x2e, 0x67, 0x6f, 0x6f, 0x67, 0x6c, 0x65, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75,
	0x66, 0x2e, 0x54, 0x69, 0x6d, 0x65, 0x73, 0x74, 0x61, 0x6d, 0x70, 0x52, 0x09, 0x75, 0x70, 0x64,
	0x61, 0x74, 0x65, 0x64, 0x41, 0x74, 0x22, 0x7d, 0x0a, 0x19, 0x43, 0x72, 0x65, 0x61, 0x74, 0x65,
	0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75,
	0x65, 0x73, 0x74, 0x12, 0x12, 0x0a, 0x04, 0x6e, 0x61, 0x6d, 0x65, 0x18, 0x01, 0x20, 0x01, 0x28,
	0x09, 0x52, 0x04, 0x6e, 0x61, 0x6d, 0x65, 0x12, 0x23, 0x0a, 0x0d, 0x65, 0x6d, 0x61, 0x69, 0x6c,
	0x5f, 0x61, 0x64, 0x64, 0x72, 0x65, 0x73, 0x73, 0x18, 0x02, 0x20, 0x01, 0x28, 0x09, 0x52, 0x0c,
	0x65, 0x6d, 0x61, 0x69, 0x6c, 0x41, 0x64, 0x64, 0x72, 0x65, 0x73, 0x73, 0x12, 0x27, 0x0a, 0x0f,
	0x70, 0x72, 0x6f, 0x66, 0x69, 0x6c, 0x65, 0x5f, 0x70, 0x69, 0x63, 0x74, 0x75, 0x72, 0x65, 0x18,
	0x03, 0x20, 0x01, 0x28, 0x0c, 0x52, 0x0e, 0x70, 0x72, 0x6f, 0x66, 0x69, 0x6c, 0x65, 0x50, 0x69,
	0x63, 0x74, 0x75, 0x72, 0x65, 0x22, 0x2c, 0x0a, 0x1a, 0x43, 0x72, 0x65, 0x61, 0x74, 0x65, 0x53,
	0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x73, 0x70, 0x6f,
	0x6e, 0x73, 0x65, 0x12, 0x0e, 0x0a, 0x02, 0x69, 0x64, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52,
	0x02, 0x69, 0x64, 0x22, 0x28, 0x0a, 0x16, 0x47, 0x65, 0x74, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68,
	0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x0e, 0x0a,
	0x02, 0x69, 0x64, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x02, 0x69, 0x64, 0x22, 0x4d, 0x0a,
	0x17, 0x47, 0x65, 0x74, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72,
	0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x12, 0x32, 0x0a, 0x0d, 0x73, 0x71, 0x75, 0x61,
	0x73, 0x68, 0x5f, 0x70, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x18, 0x02, 0x20, 0x01, 0x28, 0x0b, 0x32,
	0x0d, 0x2e, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x0c,
	0x73, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x22, 0x1c, 0x0a, 0x1a,
	0x47, 0x65, 0x74, 0x41, 0x6c, 0x6c, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79,
	0x65, 0x72, 0x73, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x22, 0x53, 0x0a, 0x1b, 0x47, 0x65,
	0x74, 0x41, 0x6c, 0x6c, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72,
	0x73, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x12, 0x34, 0x0a, 0x0e, 0x73, 0x71, 0x75,
	0x61, 0x73, 0x68, 0x5f, 0x70, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x73, 0x18, 0x01, 0x20, 0x03, 0x28,
	0x0b, 0x32, 0x0d, 0x2e, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72,
	0x52, 0x0d, 0x73, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x73, 0x22,
	0xe6, 0x01, 0x0a, 0x19, 0x55, 0x70, 0x64, 0x61, 0x74, 0x65, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68,
	0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x0e, 0x0a,
	0x02, 0x69, 0x64, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x02, 0x69, 0x64, 0x12, 0x30, 0x0a,
	0x04, 0x6e, 0x61, 0x6d, 0x65, 0x18, 0x02, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x1c, 0x2e, 0x67, 0x6f,
	0x6f, 0x67, 0x6c, 0x65, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2e, 0x53, 0x74,
	0x72, 0x69, 0x6e, 0x67, 0x56, 0x61, 0x6c, 0x75, 0x65, 0x52, 0x04, 0x6e, 0x61, 0x6d, 0x65, 0x12,
	0x41, 0x0a, 0x0d, 0x65, 0x6d, 0x61, 0x69, 0x6c, 0x5f, 0x61, 0x64, 0x64, 0x72, 0x65, 0x73, 0x73,
	0x18, 0x03, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x1c, 0x2e, 0x67, 0x6f, 0x6f, 0x67, 0x6c, 0x65, 0x2e,
	0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2e, 0x53, 0x74, 0x72, 0x69, 0x6e, 0x67, 0x56,
	0x61, 0x6c, 0x75, 0x65, 0x52, 0x0c, 0x65, 0x6d, 0x61, 0x69, 0x6c, 0x41, 0x64, 0x64, 0x72, 0x65,
	0x73, 0x73, 0x12, 0x44, 0x0a, 0x0f, 0x70, 0x72, 0x6f, 0x66, 0x69, 0x6c, 0x65, 0x5f, 0x70, 0x69,
	0x63, 0x74, 0x75, 0x72, 0x65, 0x18, 0x04, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x1b, 0x2e, 0x67, 0x6f,
	0x6f, 0x67, 0x6c, 0x65, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2e, 0x42, 0x79,
	0x74, 0x65, 0x73, 0x56, 0x61, 0x6c, 0x75, 0x65, 0x52, 0x0e, 0x70, 0x72, 0x6f, 0x66, 0x69, 0x6c,
	0x65, 0x50, 0x69, 0x63, 0x74, 0x75, 0x72, 0x65, 0x22, 0x50, 0x0a, 0x1a, 0x55, 0x70, 0x64, 0x61,
	0x74, 0x65, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x65,
	0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x12, 0x32, 0x0a, 0x0d, 0x73, 0x71, 0x75, 0x61, 0x73, 0x68,
	0x5f, 0x70, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x18, 0x01, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x0d, 0x2e,
	0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x0c, 0x73, 0x71,
	0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x22, 0x2b, 0x0a, 0x19, 0x44, 0x65,
	0x6c, 0x65, 0x74, 0x65, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72,
	0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x0e, 0x0a, 0x02, 0x69, 0x64, 0x18, 0x02, 0x20,
	0x01, 0x28, 0x09, 0x52, 0x02, 0x69, 0x64, 0x22, 0x2c, 0x0a, 0x1a, 0x44, 0x65, 0x6c, 0x65, 0x74,
	0x65, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x73,
	0x70, 0x6f, 0x6e, 0x73, 0x65, 0x12, 0x0e, 0x0a, 0x02, 0x69, 0x64, 0x18, 0x03, 0x20, 0x01, 0x28,
	0x09, 0x52, 0x02, 0x69, 0x64, 0x32, 0xb5, 0x04, 0x0a, 0x13, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68,
	0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x53, 0x65, 0x72, 0x76, 0x69, 0x63, 0x65, 0x12, 0x6c, 0x0a,
	0x12, 0x43, 0x72, 0x65, 0x61, 0x74, 0x65, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61,
	0x79, 0x65, 0x72, 0x12, 0x1a, 0x2e, 0x43, 0x72, 0x65, 0x61, 0x74, 0x65, 0x53, 0x71, 0x75, 0x61,
	0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a,
	0x1b, 0x2e, 0x43, 0x72, 0x65, 0x61, 0x74, 0x65, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c,
	0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x22, 0x1d, 0x82, 0xd3,
	0xe4, 0x93, 0x02, 0x17, 0x3a, 0x01, 0x2a, 0x22, 0x12, 0x2f, 0x76, 0x31, 0x2f, 0x73, 0x71, 0x75,
	0x61, 0x73, 0x68, 0x2f, 0x70, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x73, 0x12, 0x65, 0x0a, 0x0f, 0x47,
	0x65, 0x74, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x12, 0x17,
	0x2e, 0x47, 0x65, 0x74, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72,
	0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a, 0x18, 0x2e, 0x47, 0x65, 0x74, 0x53, 0x71, 0x75,
	0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73,
	0x65, 0x22, 0x1f, 0x82, 0xd3, 0xe4, 0x93, 0x02, 0x19, 0x22, 0x17, 0x2f, 0x76, 0x31, 0x2f, 0x73,
	0x71, 0x75, 0x61, 0x73, 0x68, 0x2f, 0x70, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x73, 0x2f, 0x7b, 0x69,
	0x64, 0x7d, 0x12, 0x66, 0x0a, 0x11, 0x4c, 0x69, 0x73, 0x74, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68,
	0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x73, 0x12, 0x1b, 0x2e, 0x47, 0x65, 0x74, 0x41, 0x6c, 0x6c,
	0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x73, 0x52, 0x65, 0x71,
	0x75, 0x65, 0x73, 0x74, 0x1a, 0x18, 0x2e, 0x47, 0x65, 0x74, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68,
	0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x22, 0x1a,
	0x82, 0xd3, 0xe4, 0x93, 0x02, 0x14, 0x12, 0x12, 0x2f, 0x76, 0x31, 0x2f, 0x73, 0x71, 0x75, 0x61,
	0x73, 0x68, 0x2f, 0x70, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x73, 0x12, 0x71, 0x0a, 0x12, 0x55, 0x70,
	0x64, 0x61, 0x74, 0x65, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72,
	0x12, 0x1a, 0x2e, 0x55, 0x70, 0x64, 0x61, 0x74, 0x65, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50,
	0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a, 0x1b, 0x2e, 0x55,
	0x70, 0x64, 0x61, 0x74, 0x65, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65,
	0x72, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x22, 0x22, 0x82, 0xd3, 0xe4, 0x93, 0x02,
	0x1c, 0x3a, 0x01, 0x2a, 0x32, 0x17, 0x2f, 0x76, 0x31, 0x2f, 0x73, 0x71, 0x75, 0x61, 0x73, 0x68,
	0x2f, 0x70, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x73, 0x2f, 0x7b, 0x69, 0x64, 0x7d, 0x12, 0x6e, 0x0a,
	0x12, 0x44, 0x65, 0x6c, 0x65, 0x74, 0x65, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c, 0x61,
	0x79, 0x65, 0x72, 0x12, 0x1a, 0x2e, 0x44, 0x65, 0x6c, 0x65, 0x74, 0x65, 0x53, 0x71, 0x75, 0x61,
	0x73, 0x68, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a,
	0x1b, 0x2e, 0x44, 0x65, 0x6c, 0x65, 0x74, 0x65, 0x53, 0x71, 0x75, 0x61, 0x73, 0x68, 0x50, 0x6c,
	0x61, 0x79, 0x65, 0x72, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x22, 0x1f, 0x82, 0xd3,
	0xe4, 0x93, 0x02, 0x19, 0x2a, 0x17, 0x2f, 0x76, 0x31, 0x2f, 0x73, 0x71, 0x75, 0x61, 0x73, 0x68,
	0x2f, 0x70, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x73, 0x2f, 0x7b, 0x69, 0x64, 0x7d, 0x42, 0x43, 0x42,
	0x0b, 0x50, 0x6c, 0x61, 0x79, 0x65, 0x72, 0x50, 0x72, 0x6f, 0x74, 0x6f, 0x50, 0x01, 0x5a, 0x32,
	0x67, 0x69, 0x74, 0x68, 0x75, 0x62, 0x2e, 0x63, 0x6f, 0x6d, 0x2f, 0x74, 0x68, 0x65, 0x73, 0x61,
	0x6d, 0x6d, 0x79, 0x32, 0x30, 0x31, 0x30, 0x2f, 0x61, 0x70, 0x69, 0x2e, 0x74, 0x68, 0x65, 0x73,
	0x61, 0x6d, 0x6d, 0x79, 0x32, 0x30, 0x31, 0x30, 0x2e, 0x63, 0x6f, 0x6d, 0x2f, 0x70, 0x72, 0x6f,
	0x74, 0x6f, 0x62, 0x06, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x33,
}

var (
	file_proto_v1_squash_player_proto_rawDescOnce sync.Once
	file_proto_v1_squash_player_proto_rawDescData = file_proto_v1_squash_player_proto_rawDesc
)

func file_proto_v1_squash_player_proto_rawDescGZIP() []byte {
	file_proto_v1_squash_player_proto_rawDescOnce.Do(func() {
		file_proto_v1_squash_player_proto_rawDescData = protoimpl.X.CompressGZIP(file_proto_v1_squash_player_proto_rawDescData)
	})
	return file_proto_v1_squash_player_proto_rawDescData
}

var file_proto_v1_squash_player_proto_msgTypes = make([]protoimpl.MessageInfo, 11)
var file_proto_v1_squash_player_proto_goTypes = []interface{}{
	(*SquashPlayer)(nil),                // 0: SquashPlayer
	(*CreateSquashPlayerRequest)(nil),   // 1: CreateSquashPlayerRequest
	(*CreateSquashPlayerResponse)(nil),  // 2: CreateSquashPlayerResponse
	(*GetSquashPlayerRequest)(nil),      // 3: GetSquashPlayerRequest
	(*GetSquashPlayerResponse)(nil),     // 4: GetSquashPlayerResponse
	(*GetAllSquashPlayersRequest)(nil),  // 5: GetAllSquashPlayersRequest
	(*GetAllSquashPlayersResponse)(nil), // 6: GetAllSquashPlayersResponse
	(*UpdateSquashPlayerRequest)(nil),   // 7: UpdateSquashPlayerRequest
	(*UpdateSquashPlayerResponse)(nil),  // 8: UpdateSquashPlayerResponse
	(*DeleteSquashPlayerRequest)(nil),   // 9: DeleteSquashPlayerRequest
	(*DeleteSquashPlayerResponse)(nil),  // 10: DeleteSquashPlayerResponse
	(*timestamppb.Timestamp)(nil),       // 11: google.protobuf.Timestamp
	(*wrapperspb.StringValue)(nil),      // 12: google.protobuf.StringValue
	(*wrapperspb.BytesValue)(nil),       // 13: google.protobuf.BytesValue
}
var file_proto_v1_squash_player_proto_depIdxs = []int32{
	11, // 0: SquashPlayer.created_at:type_name -> google.protobuf.Timestamp
	11, // 1: SquashPlayer.updated_at:type_name -> google.protobuf.Timestamp
	0,  // 2: GetSquashPlayerResponse.squash_player:type_name -> SquashPlayer
	0,  // 3: GetAllSquashPlayersResponse.squash_players:type_name -> SquashPlayer
	12, // 4: UpdateSquashPlayerRequest.name:type_name -> google.protobuf.StringValue
	12, // 5: UpdateSquashPlayerRequest.email_address:type_name -> google.protobuf.StringValue
	13, // 6: UpdateSquashPlayerRequest.profile_picture:type_name -> google.protobuf.BytesValue
	0,  // 7: UpdateSquashPlayerResponse.squash_player:type_name -> SquashPlayer
	1,  // 8: SquashPlayerService.CreateSquashPlayer:input_type -> CreateSquashPlayerRequest
	3,  // 9: SquashPlayerService.GetSquashPlayer:input_type -> GetSquashPlayerRequest
	5,  // 10: SquashPlayerService.ListSquashPlayers:input_type -> GetAllSquashPlayersRequest
	7,  // 11: SquashPlayerService.UpdateSquashPlayer:input_type -> UpdateSquashPlayerRequest
	9,  // 12: SquashPlayerService.DeleteSquashPlayer:input_type -> DeleteSquashPlayerRequest
	2,  // 13: SquashPlayerService.CreateSquashPlayer:output_type -> CreateSquashPlayerResponse
	4,  // 14: SquashPlayerService.GetSquashPlayer:output_type -> GetSquashPlayerResponse
	4,  // 15: SquashPlayerService.ListSquashPlayers:output_type -> GetSquashPlayerResponse
	8,  // 16: SquashPlayerService.UpdateSquashPlayer:output_type -> UpdateSquashPlayerResponse
	10, // 17: SquashPlayerService.DeleteSquashPlayer:output_type -> DeleteSquashPlayerResponse
	13, // [13:18] is the sub-list for method output_type
	8,  // [8:13] is the sub-list for method input_type
	8,  // [8:8] is the sub-list for extension type_name
	8,  // [8:8] is the sub-list for extension extendee
	0,  // [0:8] is the sub-list for field type_name
}

func init() { file_proto_v1_squash_player_proto_init() }
func file_proto_v1_squash_player_proto_init() {
	if File_proto_v1_squash_player_proto != nil {
		return
	}
	if !protoimpl.UnsafeEnabled {
		file_proto_v1_squash_player_proto_msgTypes[0].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*SquashPlayer); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_proto_v1_squash_player_proto_msgTypes[1].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*CreateSquashPlayerRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_proto_v1_squash_player_proto_msgTypes[2].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*CreateSquashPlayerResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_proto_v1_squash_player_proto_msgTypes[3].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*GetSquashPlayerRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_proto_v1_squash_player_proto_msgTypes[4].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*GetSquashPlayerResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_proto_v1_squash_player_proto_msgTypes[5].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*GetAllSquashPlayersRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_proto_v1_squash_player_proto_msgTypes[6].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*GetAllSquashPlayersResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_proto_v1_squash_player_proto_msgTypes[7].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*UpdateSquashPlayerRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_proto_v1_squash_player_proto_msgTypes[8].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*UpdateSquashPlayerResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_proto_v1_squash_player_proto_msgTypes[9].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*DeleteSquashPlayerRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_proto_v1_squash_player_proto_msgTypes[10].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*DeleteSquashPlayerResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
	}
	type x struct{}
	out := protoimpl.TypeBuilder{
		File: protoimpl.DescBuilder{
			GoPackagePath: reflect.TypeOf(x{}).PkgPath(),
			RawDescriptor: file_proto_v1_squash_player_proto_rawDesc,
			NumEnums:      0,
			NumMessages:   11,
			NumExtensions: 0,
			NumServices:   1,
		},
		GoTypes:           file_proto_v1_squash_player_proto_goTypes,
		DependencyIndexes: file_proto_v1_squash_player_proto_depIdxs,
		MessageInfos:      file_proto_v1_squash_player_proto_msgTypes,
	}.Build()
	File_proto_v1_squash_player_proto = out.File
	file_proto_v1_squash_player_proto_rawDesc = nil
	file_proto_v1_squash_player_proto_goTypes = nil
	file_proto_v1_squash_player_proto_depIdxs = nil
}
