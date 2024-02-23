package rbac

import (
	"database/sql"
	"fmt"
	"github.com/casbin/casbin/v2"
	"github.com/casbin/casbin/v2/model"
	casbinpgadapter "github.com/cychiuae/casbin-pg-adapter"
	"github.com/thesammy2010/api.thesammy2010.com/internal/logger"
	"go.uber.org/zap"

	"github.com/thesammy2010/api.thesammy2010.com/internal/config"
)

type Rbac struct {
	*casbin.Enforcer
}

func New(cfg config.Config) (*Rbac, error) {
	//a, err := xormadapter.NewAdapter("postgres", cfg.DatabaseURL)
	db, err := sql.Open("postgres", cfg.DatabaseURL)
	if err != nil {
		return nil, err
	}
	tableName := "casbin"
	a, err := casbinpgadapter.NewAdapter(db, tableName)
	m, err := model.NewModelFromFile("./internal/rbac/model.conf")
	if err != nil {
		return nil, err
	}
	e, err := casbin.NewEnforcer(m, a)
	return &Rbac{e}, err
}

type Resource string
type Group string
type Action string

const (
	ResourcePlayer     Resource = "squash_player"
	ResourceSingleGame Resource = "squash_game_single"
	ActionViewer       Action   = "read"
	ActionWriter       Action   = "write"
	GroupAdmin         Group    = "group_admin"
	GroupViewer        Group    = "group_viewer"
)

// TODO better system of identifying a user across routes. Can't use `X-User-Id` and `GoogleAccountId` is only availble on signup

func (rb *Rbac) HandleNewUser(googleAccountId, playerId, trace string) {
	// The user should be able to access this group at all times
	qn := fmt.Sprintf("%s-%s", ResourcePlayer, playerId)
	if _, err := rb.AddPolicy(googleAccountId, qn, string(ActionWriter)); err != nil {
		logger.Error("Error adding RBAC policy",
			zap.String("resource", qn),
			zap.String("who", googleAccountId),
			zap.String("role", string(ActionWriter)),
			zap.String("trace", trace),
			zap.Error(err))
		return
	}
	// viewers should be able to see this
	if _, err := rb.AddPolicy(string(GroupViewer), qn, string(ActionViewer)); err != nil {
		logger.Error("Error adding RBAC policy",
			zap.String("resource", qn),
			zap.String("who", string(GroupViewer)),
			zap.String("role", string(ActionViewer)),
			zap.String("trace", trace),
			zap.Error(err))
	}
	// admins need write access
	if _, err := rb.AddPolicy(string(GroupAdmin), qn, string(ActionWriter)); err != nil {
		logger.Error("Error adding RBAC policy",
			zap.String("resource", qn),
			zap.String("who", string(GroupAdmin)),
			zap.String("role", string(ActionWriter)),
			zap.String("trace", trace),
			zap.Error(err))
	}
	logger.Debug("Updated RBAC policy successfully",
		zap.String("resource", qn),
		zap.String("who", string(GroupAdmin)),
		zap.String("role", string(ActionWriter)),
		zap.String("trace", trace),
	)
}

// CleanupPolicy TODO finish
func (rb *Rbac) CleanupPolicy() {}

type Request struct {
	Subject      string
	ResourceId   string
	ResourceType Resource
	Action       Action
}

func (rb *Rbac) IsAuthorised(r *Request, trace string) bool {
	qn := fmt.Sprintf("%s-%s", string(r.ResourceType), r.ResourceId)
	if ok, err := rb.Enforce(r.Subject, qn, string(r.Action)); !ok {
		logger.Error("Error enforcing RBAC policy",
			zap.String("resource", qn),
			zap.String("who", r.Subject),
			zap.String("role", string(r.Action)),
			zap.String("trace", trace),
			zap.Error(err))
		return false
	} else {
		return ok
	}
}
