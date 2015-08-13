/*
 * Replaces the default Gazebo contact sensor with a contact
 * sensor that doesn't have the null pointer Fini() bug. See:
 *
 * https://bitbucket.org/osrf/gazebo/issues/1629/removing-model-from-plugin-crashes-with
 *
 *
 */

#include "FixedContactSensor.h"

#include "gazebo/physics/PhysicsIface.hh"
#include "gazebo/physics/World.hh"
#include "gazebo/physics/Collision.hh"
#include "gazebo/physics/ContactManager.hh"
#include "gazebo/physics/PhysicsEngine.hh"
#include "gazebo/sensors/SensorFactory.hh"

using namespace gazebo;
using namespace sensors;

GZ_REGISTER_STATIC_SENSOR("contact", FixedContactSensor)

void FixedContactSensor::Load(const std::string &_worldName) {
	ContactSensor::Load(_worldName);
	this->StoreFilterName();
}

void FixedContactSensor::Load(const std::string &_worldName,
				  sdf::ElementPtr _sdf) {
	ContactSensor::Load(_worldName, _sdf);
	this->StoreFilterName();
}

void FixedContactSensor::StoreFilterName() {
	std::string entityName =
			this->world->GetEntity(this->parentName)->GetScopedName();
	filterName_ = entityName + "::" + this->GetName();
}

// Overrides Fini() replacing the null pointer code
void FixedContactSensor::Fini() {
	if (this->world && this->world->GetRunning())
	{
		physics::ContactManager *mgr =
				this->world->GetPhysicsEngine()->GetContactManager();
		mgr->RemoveFilter(filterName_);
	}

	// HACK Temporarily unset the world pointer on this sensor
	// to make sure the default filter remove code won't run
	// when calling the parent method.
	// Unfortunately we need to call parent since `contactSub`
	// and `contactPub` are private. It *seems* that this->world
	// is not used in any parent Fini() calls, so let's hope
	// that is indeed the case. I haven't been able to figure
	// out who resets the world pointer, so this might result
	// in a lingering pointer - for the world, which is sort
	// of a non-issue.
	auto oldPtr = this->world;
	this->world = physics::WorldPtr();
	ContactSensor::Fini();
	this->world = oldPtr;
}
