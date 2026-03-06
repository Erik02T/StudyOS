from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class OrganizationOut(BaseModel):
    id: int
    name: str
    slug: str
    role: str


class OrganizationMemberOut(BaseModel):
    user_id: int
    email: str
    role: str


class OrganizationMemberListResponse(BaseModel):
    items: list[OrganizationMemberOut]
    total: int
    page: int
    page_size: int
    pages: int


class OrganizationMemberInvite(BaseModel):
    email: str
    role: str = Field(default="member", pattern="^(owner|admin|member)$")


class OrganizationMemberRoleUpdate(BaseModel):
    role: str = Field(pattern="^(owner|admin|member)$")
