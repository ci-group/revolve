//=================================================================================================
//                  Copyright (C) 2018 Alain Lanthier - All Rights Reserved  
//                  License: MIT License    See LICENSE.md for the full license.
//                  Original code 2017 Olivier Mallet (MIT License)              
//=================================================================================================

#ifndef PARAMETER_H
#define PARAMETER_H

namespace galgo {

// end of recursion for computing the sum of a parameter pack of integral numbers
int sum(int first) 
{
   return first;
}

// recursion for computing the sum of a parameter pack of integral numbers
template <typename...Args>
int sum(int first, Args...args) 
{
   return first + sum(args...);
}

/*-------------------------------------------------------------------------------------------------*/

// abstract base class for Parameter objects 
template <typename T>
class BaseParameter
{
public:
   virtual ~BaseParameter() {}
   virtual std::string encode() const = 0;
   virtual std::string encode(T z) const = 0;
   virtual T decode(const std::string& y) const = 0;
   virtual int size() const = 0;
   virtual const std::vector<T>& getData() const = 0;
};

/*-------------------------------------------------------------------------------------------------*/

template <typename T, int N>
class Parameter : public BaseParameter<T>
{
   template <typename K>
   friend class Chromosome;

private:
   std::vector<T>   data;               // contains lower bound, upper bound and initial value (optional)

public:
   // default constructor
   Parameter()
   {
   }

   // constructor
   Parameter(const std::vector<T>& data)
   {
      if (data.size() < 2) {
         throw std::invalid_argument("Error: in class galgo::Parameter<T,N>, argument must contain at least 2 elements of type T, the lower bound and the upper bound, please adjust.");
      }
      if (data[0] >= data[1]) {
         throw std::invalid_argument("Error: in class galgo::Parameter<T,N>, first argument (lower bound) cannot be equal or greater than second argument (upper bound), please amend.");
      }
      this->data = data;
   }
   // return encoded parameter size in number of bits
   int size() const override {
      return N;
   }
   // return parameter initial data
   const std::vector<T>& getData() const override {
      return data;
   }


private:
   // encoding random unsigned integer
   std::string encode() const override 
   {
      std::string str = GetBinary(galgo::Randomize<N>::generate());
      return str.substr(str.size() - N, N);
   }

   // encoding known unsigned integer
   std::string encode(T z) const override 
   {
       if (std::is_integral<T>::value)
       {
           uint64_t value = (uint64_t)(z - data[0]);
           std::string str = GetBinary(value);
           return str.substr(str.size() - N, N);
       }
       else
       {
           uint64_t value = (uint64_t)(Randomize<N>::MAXVAL * (z - data[0]) / (data[1] - data[0]));
           std::string str = GetBinary(value);
           return str.substr(str.size() - N, N);
       }
   }

   // decoding string 
   T decode(const std::string& str) const override 
   {
       if (std::is_integral<T>::value)
       {
           int64_t d0 = (int64_t)data[0];
           int64_t r = d0 + GetValue(str);
           int64_t v = std::min<int64_t>(std::max<int64_t>(r, static_cast<int64_t>(data[0])), static_cast<int64_t>(data[1]));
           return (T)v;
       }
       else
       {
           // decoding string to real value
           // Randomize<N>::MAXVAL=> 0,1,3,7,15,31,...
           return (T)(data[0] + (GetValue(str) / static_cast<double>(Randomize<N>::MAXVAL)) * (data[1] - data[0]));
       }
   }
};

//=================================================================================================

}

#endif
