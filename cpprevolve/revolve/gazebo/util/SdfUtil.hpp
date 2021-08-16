#include <sdf/Element.hh>

namespace revolve
{
    namespace gazebo
    {

        // Gets an attribute from an sdf element
        // Throws std::runtime_error when not present.
        // Can do types:
        // - 'std::string'
        // - 'bool'
        // - 'double'
        template <typename OfType>
        OfType getSdfAttrSafe(sdf::ElementPtr sdf, std::string const &attribute)
        {
            static_assert(
                std::is_same<OfType, std::string>::value ||
                    std::is_same<OfType, double>::value ||
                    std::is_same<OfType, bool>::value,
                "Type not supported");
            if (!sdf->HasAttribute(attribute) || !sdf->GetAttribute(attribute)->IsType<OfType>())
            {
                throw std::runtime_error(std::string("Could not get attribute: ") + attribute);
            }
            else
            {
                if constexpr (std::is_same<OfType, std::string>::value)
                {
                    return sdf->GetAttribute(attribute)->GetAsString();
                }
                else
                {
                    // Did not test this part yet
                    OfType buffer;
                    return sdf->GetAttribute(attribute)->Get<OfType>(buffer);
                }
            }
        }

    }
}
