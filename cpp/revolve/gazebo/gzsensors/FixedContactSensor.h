//
// Created by elte on 13-8-15.
//

#ifndef REVOLVE_FIXEDCONTACTSENSOR_H
#define REVOLVE_FIXEDCONTACTSENSOR_H

#include <gazebo/sensors/ContactSensor.hh>

namespace gazebo {
namespace sensors {

class FixedContactSensor: public ContactSensor {
public:
	// Override both Load methods to store the filter name
	virtual void Load(const std::string &_worldName);

	virtual void Load(const std::string &_worldName,
						  	sdf::ElementPtr _sdf);

protected:
	virtual void Fini();

private:
	// Stores the name of the filter so it can be recovered
	// even after the parent entity has been deleted.
	std::string filterName_;

	void StoreFilterName();
};

}
}

#endif //REVOLVE_FIXEDCONTACTSENSOR_H
