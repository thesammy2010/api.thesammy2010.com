package rbac

import (
	"fmt"
	"github.com/casbin/casbin/v2"
	"github.com/casbin/casbin/v2/model"
	xormadapter "github.com/casbin/xorm-adapter/v2"
	"github.com/google/uuid"
	"github.com/thesammy2010/api.thesammy2010.com/internal/logger"
	"go.uber.org/zap"

	"github.com/thesammy2010/api.thesammy2010.com/internal/config"
)

type Rbac struct {
	*casbin.Enforcer
}

func New(cfg config.Config) (*Rbac, error) {
	a, err := xormadapter.NewAdapter("postgres", cfg.DatabaseURL)
	if err != nil {
		return nil, err
	}
	m, err := model.NewModelFromFile("./model.conf")
	if err != nil {
		return nil, err
	}
	e, err := casbin.NewEnforcer(m, a)
	return &Rbac{e}, err
}

type Resource string

const (
	Player     Resource = "SquashPlayer"
	SingleGame          = "SingleGame"
)

type Action string

const (
	ActionGet    Action = "GET"
	ActionList          = "LIST"
	ActionUpdate        = "UPDATE"
	ActionDelete        = "DELETE"
	ActionCreate        = "CREATE"
)

type ResourceRequest struct {
	Subject  uuid.UUID
	Resource Resource
	Action   Action
}

func (r *ResourceRequest) String() string {
	return fmt.Sprintf("Request(Subject=`%v`,Resource=`%s`,Action=`%s`)", r.Subject, r.Resource, r.Action)
}

func (rb *Rbac) GetAccess(r *ResourceRequest) bool {
	ok, err := rb.Enforce(r.Subject, r.Resource, r.Action)
	if err != nil {
		logger.Error("Error enforcing RBAC policy", zap.String("RBAC", r.String()), zap.Error(err))
		return false
	}
	return ok
}

func (rb *Rbac) SetAccessGranted(r *ResourceRequest) bool {
	ok, err := rb.AddPolicy(r.Subject, r.Resource, r.Action)
	if err != nil {
		logger.Error("Error adding RBAC policy", zap.String("RBAC", r.String()), zap.Error(err))
		return false
	}
	return ok
}
